import time
import re
from sqlalchemy import select
from app.models import User
from app.security import passwords
from conftest import login, csrf, PASSWORD


def test_register_login_normalization_hashing_and_logout(client, application):
    auth = login(client, "STUDENT@example.com")
    user = client.get("/api/auth/me", headers=auth).json()
    assert user["email"] == "student@example.com"

    async def check():
        async with application.state.sessions() as db:
            stored = await db.scalar(select(User))
            assert stored.hashed_password != PASSWORD
            assert passwords.verify(PASSWORD, stored.hashed_password)

    client.portal.call(check)
    assert client.post("/api/auth/logout", headers=csrf(client)).status_code == 200
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_refresh_rotates_cookie_and_rejects_replay(client):
    auth = login(client)
    raw = client.cookies.get("studymind_refresh")
    nonce = csrf(client)
    refreshed = client.post("/api/auth/refresh", headers=nonce)
    assert refreshed.status_code == 200
    assert client.cookies.get("studymind_refresh") != raw
    replay = client.post(
        "/api/auth/refresh",
        headers={
            **nonce,
            "Cookie": f"studymind_refresh={raw}; studymind_csrf={nonce['X-CSRF-Token']}",
        },
    )
    assert replay.status_code == 401
    assert client.get("/api/auth/me", headers=auth).status_code == 200


def test_csrf_origin_schema_and_secret_errors(client):
    assert (
        client.post(
            "/api/auth/login", json={"email": "x@example.com", "password": "x"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "x@example.com", "password": "secret"},
            headers={**csrf(client), "Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    invalid = client.post(
        "/api/auth/register",
        json={"email": "bad", "password": "do-not-echo"},
        headers=csrf(client),
    )
    assert invalid.status_code == 422
    assert "do-not-echo" not in invalid.text
    assert (
        client.get("/api/health", headers={"Host": "evil.example"}).status_code == 421
    )
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"


def test_change_password_revokes_access_and_refresh(client):
    auth = login(client)
    old_cookie = client.cookies.get("studymind_refresh")
    response = client.post(
        "/api/auth/change-password",
        headers=auth,
        json={"current_password": PASSWORD, "new_password": "another long passphrase"},
    )
    assert response.status_code == 200, response.text
    assert client.get("/api/auth/me", headers=auth).status_code == 401
    assert (
        client.post(
            "/api/auth/login",
            headers=csrf(client),
            json={"email": "student@example.com", "password": PASSWORD},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login",
            headers=csrf(client),
            json={
                "email": "student@example.com",
                "password": "another long passphrase",
            },
        ).status_code
        == 200
    )


def test_password_recovery_single_use_and_no_enumeration(client, application):
    auth = login(client)
    mail = []
    application.state.settings.smtp_host = "mail.test"
    application.state.settings.smtp_from = "support@example.com"

    async def mailer(config, to, subject, body):
        mail.append(body)

    application.state.mailer = mailer
    existing = client.post(
        "/api/auth/forgot-password",
        headers=csrf(client),
        json={"email": "student@example.com"},
    )
    absent = client.post(
        "/api/auth/forgot-password",
        headers=csrf(client),
        json={"email": "absent@example.com"},
    )
    assert existing.status_code == absent.status_code == 202
    assert existing.json() == absent.json()
    token = re.search(r"#token=([a-f0-9]{64})", mail[0]).group(1)
    body = {"token": token, "new_password": "a reset long passphrase"}
    assert (
        client.post(
            "/api/auth/reset-password", headers=csrf(client), json=body
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/reset-password", headers=csrf(client), json=body
        ).status_code
        == 400
    )
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_verification_requires_emailed_token_and_chosen_password(client, application):
    application.state.settings.require_email_verification = True
    application.state.settings.smtp_host = "mail.test"
    application.state.settings.smtp_from = "support@example.com"
    mail = []

    async def mailer(config, to, subject, body):
        mail.append(body)

    application.state.mailer = mailer
    body = {"email": "new@example.com", "password": PASSWORD}
    nonce = csrf(client)
    assert (
        client.post("/api/auth/register", headers=nonce, json=body).status_code == 202
    )
    assert client.post("/api/auth/login", headers=nonce, json=body).status_code == 403
    token = re.search(r"#token=([a-f0-9]{64})", mail[0]).group(1)
    assert (
        client.post(
            "/api/auth/verify-email",
            headers=nonce,
            json={"token": token, "password": "wrong password"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/auth/verify-email",
            headers=nonce,
            json={"token": token, "password": PASSWORD},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/verify-email",
            headers=nonce,
            json={"token": token, "password": PASSWORD},
        ).status_code
        == 400
    )
    assert client.post("/api/auth/login", headers=nonce, json=body).status_code == 200


def test_recovery_unconfigured_fails_honestly(client):
    response = client.post(
        "/api/auth/forgot-password",
        headers=csrf(client),
        json={"email": "nobody@example.com"},
    )
    assert response.status_code == 503


def test_switching_accounts_in_one_browser_revokes_its_previous_session(client):
    first = login(client, "first@example.com")
    login(client, "second@example.com")
    assert client.get("/api/auth/me", headers=first).status_code == 401


def test_unicode_password_is_not_silently_truncated(client):
    password = "🌱" * 40
    auth = login(client, "unicode@example.com", password)
    assert client.get("/api/auth/me", headers=auth).status_code == 200
    assert (
        client.post(
            "/api/auth/login",
            headers=csrf(client),
            json={"email": "unicode@example.com", "password": password + "x"},
        ).status_code
        == 401
    )


def test_invalid_jwt_claims_are_rejected(client, application):
    import jwt

    auth = login(client)
    claims = jwt.decode(
        auth["Authorization"].split()[1], options={"verify_signature": False}
    )
    for update in (
        {"exp": 0},
        {"aud": "other-app"},
        {"sid": "not-a-uuid"},
        {"iat": int(time.time()) + 3600},
    ):
        forged = jwt.encode(
            {**claims, **update},
            application.state.settings.secret_key,
            algorithm="HS256",
        )
        assert (
            client.get(
                "/api/auth/me", headers={"Authorization": "Bearer " + forged}
            ).status_code
            == 401
        )
