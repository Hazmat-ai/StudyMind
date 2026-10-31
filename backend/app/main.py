import asyncio
import logging
import secrets
from contextlib import asynccontextmanager
import anyio
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from .config import Settings
from .database import configure_database, Base
from .security import passwords
from .middleware import SecurityMiddleware
from .services.mail import send_email
from .routers import auth, generate, studysets

logger = logging.getLogger("studymind")


def create_app(config: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        app.state.settings = config or Settings()
        app.state.engine, app.state.sessions = configure_database(
            app.state.settings.database_url
        )
        app.state.mailer = send_email
        app.state.pdf_slots = asyncio.Semaphore(1)
        app.state.dummy_password = await anyio.to_thread.run_sync(
            passwords.hash, secrets.token_urlsafe(24)
        )
        try:
            async with app.state.engine.begin() as connection:
                if app.state.settings.test_auto_schema:
                    await connection.run_sync(Base.metadata.create_all)
                else:
                    try:
                        version = (
                            await connection.execute(
                                text("SELECT version_num FROM alembic_version")
                            )
                        ).scalar_one()
                    except Exception as error:
                        raise RuntimeError(
                            "Run alembic upgrade head before starting StudyMind"
                        ) from error
                    if version != "0001":
                        raise RuntimeError(
                            "Database schema does not match this application"
                        )
            async with app.state.sessions() as db:
                await db.execute(
                    text(
                        "INSERT INTO generation_quota(id) VALUES ('global') ON CONFLICT(id) DO NOTHING"
                    )
                )
                await db.commit()
            yield
        finally:
            await app.state.engine.dispose()

    app = FastAPI(
        title="StudyMind API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if config and not config.production else None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(SecurityMiddleware)
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(generate.router, prefix="/api/generate", tags=["Generation"])
    app.include_router(studysets.router, prefix="/api/studysets", tags=["Study sets"])

    @app.get("/api/health")
    async def health(request: Request):
        async with request.app.state.sessions() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok"}

    @app.get("/api/config")
    async def capabilities(request: Request):
        config = request.app.state.settings
        return {
            "generation_ready": bool(
                config.anthropic_api_key and config.anthropic_model
            ),
            "email_ready": config.mail_ready,
            "verification_required": config.require_email_verification,
            "max_content_chars": 12000,
            "max_pdf_bytes": 5 * 1024 * 1024,
        }

    @app.exception_handler(RequestValidationError)
    async def invalid(request, error):
        return JSONResponse(
            {
                "detail": "Check the request fields and limits",
                "fields": [
                    ".".join(str(p) for p in e["loc"]) for e in error.errors()[:10]
                ],
                "request_id": getattr(request.state, "request_id", ""),
            },
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unexpected(request, error):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "Unhandled failure request_id=%s error_type=%s",
            request_id,
            type(error).__name__,
        )
        return JSONResponse(
            {
                "detail": "The request could not be completed. Please retry later.",
                "request_id": request_id,
            },
            status_code=500,
        )

    return app


app = create_app()
