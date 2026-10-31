import logging
import secrets
import time
import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models import User, AuthSession, AccountToken
from ..schemas.auth import (
    UserCreate,
    Login,
    UserBase,
    UserDisplay,
    Token,
    PasswordChange,
    PasswordReset,
    VerifyToken,
    DeleteAccount,
)
from ..security import (
    settings,
    passwords,
    digest,
    access_token,
    get_current_user,
    require_csrf,
    cookie_names,
    TOKEN_PATTERN,
    rate_limit,
)

router = APIRouter()
logger = logging.getLogger("studymind.auth")


async def hashed(password: str) -> str:
    return await anyio.to_thread.run_sync(passwords.hash, password)


async def verify(password: str, hashed_password: str) -> bool:
    try:
        return await anyio.to_thread.run_sync(
            passwords.verify, password, hashed_password
        )
    except (ValueError, TypeError):
        return False


def set_refresh(response: Response, raw: str, config, max_age: int = 7 * 86400) -> None:
    refresh, _ = cookie_names(config)
    response.set_cookie(
        refresh,
        raw,
        max_age=max_age,
        httponly=True,
        secure=config.production,
        samesite="lax",
        path="/",
    )


def clear_cookies(response: Response, config) -> None:
    for name in cookie_names(config):
        response.delete_cookie(
            name, path="/", secure=config.production, httponly=True, samesite="lax"
        )


def token_response(user, session, config):
    return Token(
        access_token=access_token(user, session, config),
        expires_in=config.access_token_expire_minutes * 60,
        user=UserDisplay.model_validate(user),
    )


async def issue_mail(request: Request, db: AsyncSession, user: User, kind: str) -> None:
    raw = secrets.token_hex(32)
    await db.execute(
        delete(AccountToken).where(
            AccountToken.user_id == user.id, AccountToken.kind == kind
        )
    )
    db.add(
        AccountToken(
            token_hash=digest(raw),
            user_id=user.id,
            kind=kind,
            expires=int(time.time()) + 1800,
        )
    )
    await db.commit()
    path = "verify" if kind == "verify" else "reset"
    link = f"{settings(request).web_origin}/auth/{path}#token={raw}"
    try:
        await request.app.state.mailer(
            settings(request),
            user.email,
            "StudyMind account " + path,
            f"Use this link within 30 minutes: {link}\nIf you did not request this, ignore it. Verification also requires your chosen password.",
        )
    except Exception:
        logger.error(
            "Account email delivery failed request_id=%s",
            getattr(request.state, "request_id", "unknown"),
        )


@router.get("/csrf")
async def csrf(request: Request, response: Response):
    _, name = cookie_names(settings(request))
    raw = request.cookies.get(name, "")
    if not TOKEN_PATTERN.fullmatch(raw):
        raw = secrets.token_hex(32)
    response.set_cookie(
        name,
        raw,
        max_age=7 * 86400,
        httponly=True,
        secure=settings(request).production,
        samesite="lax",
        path="/",
    )
    return {"csrf_token": raw}


@router.post("/register", dependencies=[Depends(require_csrf)], status_code=202)
async def register(
    data: UserCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    config = settings(request)
    await rate_limit(request, "register:" + request.state.client_ip, 10, 3600)
    if config.require_email_verification and not config.mail_ready:
        raise HTTPException(503, "Account email delivery is not configured")
    user = await db.scalar(select(User).where(User.email == data.email))
    if user is None:
        user = User(
            email=data.email,
            hashed_password=await hashed(data.password),
            verified=not config.require_email_verification,
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            user = await db.scalar(select(User).where(User.email == data.email))
    if user is not None and not user.verified:
        await rate_limit(request, "verify-mail:" + data.email, 3, 3600)
        await issue_mail(request, db, user, "verify")
    return {
        "message": "If this address needs verification, check your inbox. Otherwise, sign in or use password recovery.",
        "verification_required": config.require_email_verification,
    }


@router.post("/login", response_model=Token, dependencies=[Depends(require_csrf)])
async def login(
    data: Login,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    config = settings(request)
    await rate_limit(request, "login-ip:" + request.state.client_ip, 20, 300)
    await rate_limit(request, "login-account:" + data.email, 10, 300)
    user = await db.scalar(
        select(User).where(User.email == data.email).with_for_update()
    )
    # Equal expensive verification work for unknown accounts.
    target = user.hashed_password if user else request.app.state.dummy_password
    valid = await verify(data.password, target)
    if user is None or not valid:
        raise HTTPException(401, "Incorrect email or password")
    if not user.verified:
        raise HTTPException(403, "Verify your email before signing in")
    if passwords.needs_update(user.hashed_password):
        user.hashed_password = await hashed(data.password)
    old_raw = request.cookies.get(cookie_names(config)[0], "")
    if TOKEN_PATTERN.fullmatch(old_raw):
        await db.execute(
            delete(AuthSession).where(AuthSession.refresh_hash == digest(old_raw))
        )
    raw = secrets.token_hex(32)
    session = AuthSession(
        user_id=user.id, refresh_hash=digest(raw), expires=int(time.time()) + 7 * 86400
    )
    db.add(session)
    await db.commit()
    set_refresh(response, raw, config)
    return token_response(user, session, config)


@router.post("/refresh", response_model=Token, dependencies=[Depends(require_csrf)])
async def refresh(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    config = settings(request)
    name, _ = cookie_names(config)
    raw = request.cookies.get(name, "")
    if not TOKEN_PATTERN.fullmatch(raw):
        raise HTTPException(401, "Sign in to continue")
    session = await db.scalar(
        select(AuthSession)
        .where(
            AuthSession.refresh_hash == digest(raw),
            AuthSession.expires > int(time.time()),
        )
        .with_for_update()
    )
    if session is None:
        raise HTTPException(401, "Your session expired. Sign in again")
    user = await db.get(User, session.user_id)
    if user is None or not user.verified:
        raise HTTPException(401, "Sign in to continue")
    new_raw = secrets.token_hex(32)
    session.refresh_hash = digest(new_raw)
    await db.commit()
    set_refresh(
        response, new_raw, config, max_age=max(0, session.expires - int(time.time()))
    )
    return token_response(user, session, config)


@router.post("/logout", dependencies=[Depends(require_csrf)])
async def logout(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    name, _ = cookie_names(settings(request))
    raw = request.cookies.get(name, "")
    if TOKEN_PATTERN.fullmatch(raw):
        await db.execute(
            delete(AuthSession).where(AuthSession.refresh_hash == digest(raw))
        )
        await db.commit()
    clear_cookies(response, settings(request))
    return {"logged_out": True}


@router.get("/me", response_model=UserDisplay)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", dependencies=[Depends(require_csrf)], status_code=202)
async def forgot(data: UserBase, request: Request, db: AsyncSession = Depends(get_db)):
    if not settings(request).mail_ready:
        raise HTTPException(503, "Password recovery email is not configured")
    await rate_limit(request, "reset-ip:" + request.state.client_ip, 10, 3600)
    await rate_limit(request, "reset-email:" + data.email, 3, 3600)
    user = await db.scalar(select(User).where(User.email == data.email))
    if user:
        await issue_mail(request, db, user, "reset")
    return {
        "message": "If this address has an account, check your inbox. If no email arrives, retry later."
    }


@router.post(
    "/resend-verification", dependencies=[Depends(require_csrf)], status_code=202
)
async def resend(data: UserBase, request: Request, db: AsyncSession = Depends(get_db)):
    if not settings(request).mail_ready:
        raise HTTPException(503, "Account email delivery is not configured")
    await rate_limit(request, "verify-ip:" + request.state.client_ip, 10, 3600)
    await rate_limit(request, "verify-mail:" + data.email, 3, 3600)
    user = await db.scalar(select(User).where(User.email == data.email))
    if user and not user.verified:
        await issue_mail(request, db, user, "verify")
    return {"message": "If this account needs verification, check your inbox."}


async def account_token(db, raw, kind):
    token = await db.scalar(
        select(AccountToken)
        .where(
            AccountToken.token_hash == digest(raw),
            AccountToken.kind == kind,
            AccountToken.expires > int(time.time()),
        )
        .with_for_update()
    )
    if token is None:
        raise HTTPException(400, "This link expired or was already used")
    user = await db.scalar(
        select(User).where(User.id == token.user_id).with_for_update()
    )
    if user is None:
        raise HTTPException(400, "This link is unavailable")
    return token, user


@router.post("/verify-email", dependencies=[Depends(require_csrf)])
async def verify_email(data: VerifyToken, db: AsyncSession = Depends(get_db)):
    token, user = await account_token(db, data.token, "verify")
    if not await verify(data.password, user.hashed_password):
        raise HTTPException(
            400,
            "The password does not match this verification request. Use password recovery if needed.",
        )
    user.verified = True
    await db.delete(token)
    await db.commit()
    return {"verified": True}


@router.post("/reset-password", dependencies=[Depends(require_csrf)])
async def reset(data: PasswordReset, db: AsyncSession = Depends(get_db)):
    token, user = await account_token(db, data.token, "reset")
    user.hashed_password = await hashed(data.new_password)
    user.verified = True
    await db.execute(delete(AccountToken).where(AccountToken.user_id == user.id))
    await db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    await db.commit()
    return {"message": "Password updated. Sign in with your new password."}


@router.post("/change-password")
async def change(
    data: PasswordChange,
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not await verify(data.current_password, user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")
    user.hashed_password = await hashed(data.new_password)
    await db.execute(delete(AccountToken).where(AccountToken.user_id == user.id))
    await db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    await db.commit()
    clear_cookies(response, settings(request))
    return {"message": "Password updated. Sign in again on your devices."}


@router.delete("/account")
async def delete_account(
    data: DeleteAccount,
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not await verify(data.password, user.hashed_password):
        raise HTTPException(400, "Password is incorrect")
    await db.delete(user)
    await db.commit()
    clear_cookies(response, settings(request))
    return {"deleted": True}
