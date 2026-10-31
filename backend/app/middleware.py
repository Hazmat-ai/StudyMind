import logging
import hmac
import ipaddress
import uuid
from urllib.parse import urlsplit
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from fastapi import HTTPException
from .security import rate_limit, TOKEN_PATTERN


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        config = scope["app"].state.settings
        headers = {
            k.decode("latin1").lower(): v.decode("latin1")
            for k, v in scope.get("headers", [])
        }
        request_id = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        origin = headers.get("origin")
        allowed_origins = {config.web_origin, config.api_origin}
        security = {
            "x-request-id": request_id,
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "no-referrer",
            "permissions-policy": "camera=(), microphone=(), geolocation=()",
            "content-security-policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'",
        }
        if config.production:
            security["strict-transport-security"] = "max-age=31536000"
        if not config.production and scope["path"] == "/docs":
            security["content-security-policy"] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com"
            )
        if scope["path"].startswith("/api/"):
            security["cache-control"] = "no-store"
        if origin in allowed_origins:
            security.update(
                {
                    "access-control-allow-origin": origin,
                    "access-control-allow-credentials": "true",
                    "access-control-expose-headers": "X-Request-Id, Retry-After",
                    "vary": "Origin",
                }
            )
        started = False

        async def secured(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                existing = [
                    (k, v)
                    for k, v in message.get("headers", [])
                    if k.decode().lower() not in security
                ]
                message["headers"] = existing + [
                    (k.encode(), v.encode()) for k, v in security.items()
                ]
            await send(message)

        async def fail(status, detail, extra=None):
            await JSONResponse(
                {"detail": detail, "request_id": request_id},
                status_code=status,
                headers=extra,
            )(scope, receive, secured)

        try:
            host = urlsplit("//" + headers.get("host", "")).hostname
        except ValueError:
            return await fail(421, "Unexpected request host")
        trusted_hosts = {
            urlsplit(config.api_origin).hostname,
            urlsplit(config.web_origin).hostname,
        }
        if host not in trusted_hosts:
            return await fail(421, "Unexpected request host")
        if origin and origin not in allowed_origins:
            return await fail(403, "Origin is not permitted")
        if (
            scope["method"] not in ("GET", "HEAD", "OPTIONS")
            and origin not in allowed_origins
        ):
            return await fail(403, "A trusted Origin header is required")
        if headers.get("sec-fetch-site") == "cross-site":
            return await fail(
                403,
                "Cross-site requests are not supported; use the same-origin API proxy",
            )
        if scope["method"] == "OPTIONS":
            if origin not in allowed_origins:
                return await fail(403, "Origin is not permitted")
            security.update(
                {
                    "access-control-allow-methods": "GET, POST, PATCH, DELETE, OPTIONS",
                    "access-control-allow-headers": "Authorization, Content-Type, X-CSRF-Token, Idempotency-Key",
                    "access-control-max-age": "600",
                }
            )
            return await Response(status_code=204)(scope, receive, secured)
        ip = (scope.get("client") or ("unknown", 0))[0]
        supplied = headers.get("x-studymind-proxy-token", "")
        if (
            config.proxy_token
            and TOKEN_PATTERN.fullmatch(supplied)
            and hmac.compare_digest(config.proxy_token, supplied)
        ):
            try:
                ip = str(ipaddress.ip_address(headers.get("x-real-ip", "")))
            except ValueError:
                pass
        scope["state"]["client_ip"] = ip
        if scope["path"].startswith("/api/") and scope["path"] != "/api/health":
            try:
                await rate_limit(Request(scope), "ip:" + ip, 180)
            except HTTPException as error:
                return await fail(error.status_code, error.detail, error.headers)
            except Exception:
                return await fail(503, "Service temporarily unavailable")
        maximum = (
            6 * 1024 * 1024 if scope["path"] == "/api/generate/extract-pdf" else 65536
        )
        try:
            if int(headers.get("content-length", "0")) > maximum:
                return await fail(413, "Request is too large")
        except ValueError:
            return await fail(400, "Invalid request size")
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > maximum:
                return await fail(413, "Request is too large")
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        consumed = False

        async def replay():
            nonlocal consumed
            if consumed:
                return await receive()
            consumed = True
            return {
                "type": "http.request",
                "body": b"".join(chunks),
                "more_body": False,
            }

        try:
            await self.app(scope, replay, secured)
        except Exception as error:
            logging.getLogger("studymind").error(
                "Request failed request_id=%s error_type=%s",
                request_id,
                type(error).__name__,
            )
            if started:
                raise
            await fail(500, "The request could not be completed. Please retry later.")
