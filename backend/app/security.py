import hashlib
import hmac
import secrets
import time
from uuid import UUID
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .models import User, AuthSession

passwords = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
TOKEN_PATTERN = __import__("re").compile(r"^[a-f0-9]{64}$")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def settings(request: Request):
    return request.app.state.settings


def cookie_names(config):
    prefix = "__Host-" if config.production else ""
    return prefix + "studymind_refresh", prefix + "studymind_csrf"


def require_csrf(request: Request) -> None:
    _, name = cookie_names(settings(request))
    cookie = request.cookies.get(name, "")
    header = request.headers.get("x-csrf-token", "")
    if (
        not TOKEN_PATTERN.fullmatch(cookie)
        or not TOKEN_PATTERN.fullmatch(header)
        or not hmac.compare_digest(cookie, header)
    ):
        raise HTTPException(403, "Refresh your session and retry this action")


def access_token(user: User, session: AuthSession, config) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": str(user.id),
            "sid": str(session.id),
            "jti": secrets.token_hex(16),
            "iat": now,
            "exp": now + config.access_token_expire_minutes * 60,
            "iss": "studymind-api",
            "aud": "studymind-web",
        },
        config.secret_key,
        algorithm="HS256",
    )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        if credentials is None:
            raise ValueError()
        claims = jwt.decode(
            credentials.credentials,
            settings(request).secret_key,
            algorithms=["HS256"],
            audience="studymind-web",
            issuer="studymind-api",
            options={"require": ["exp", "iat", "sub", "sid", "jti", "aud", "iss"]},
        )
        user_id, session_id = UUID(claims["sub"]), UUID(claims["sid"])
        if claims["iat"] > int(time.time()) + 30:
            raise ValueError()
    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            401, "Sign in to continue", headers={"WWW-Authenticate": "Bearer"}
        )
    row = (
        await db.execute(
            select(User, AuthSession)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(
                User.id == user_id,
                AuthSession.id == session_id,
                AuthSession.expires > int(time.time()),
                User.verified.is_(True),
            )
        )
    ).first()
    if not row:
        raise HTTPException(401, "Your session expired. Sign in again")
    request.state.session_id = session_id
    return row[0]


async def rate_limit(request: Request, name: str, limit: int, period: int = 60) -> None:
    now = int(time.time())
    key = digest(name)
    async with request.app.state.sessions() as db:
        count = (
            await db.execute(
                text("""INSERT INTO rate_limits(key,count,window_end) VALUES (:key,1,:end)
        ON CONFLICT(key) DO UPDATE SET count=CASE WHEN rate_limits.window_end<=:now THEN 1 ELSE rate_limits.count+1 END,
        window_end=CASE WHEN rate_limits.window_end<=:now THEN :end ELSE rate_limits.window_end END RETURNING count"""),
                {"key": key, "now": now, "end": now + period},
            )
        ).scalar_one()
        await db.commit()
    if count > limit:
        raise HTTPException(
            429,
            "Too many requests. Please wait before retrying",
            headers={"Retry-After": str(period)},
        )
