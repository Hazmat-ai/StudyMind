"""Run hourly with the application's environment: python -m app.maintenance."""

import asyncio
import time
from sqlalchemy import delete, update
from .config import Settings
from .database import configure_database
from .models import AuthSession, AccountToken, RateLimit, GenerationJob, GenerationEvent


async def main() -> None:
    config = Settings()
    engine, sessions = configure_database(config.database_url)
    now = int(time.time())
    try:
        async with sessions() as db:
            for model in (AuthSession, AccountToken):
                await db.execute(delete(model).where(model.expires <= now))
            await db.execute(delete(RateLimit).where(RateLimit.window_end <= now))
            await db.execute(
                update(GenerationJob)
                .where(
                    GenerationJob.state == "pending", GenerationJob.created <= now - 180
                )
                .values(state="failed")
            )
            await db.execute(
                update(GenerationJob)
                .where(GenerationJob.created <= now - 3600)
                .values(result=None)
            )
            # Preserve reservations for the complete rolling quota period.
            await db.execute(
                delete(GenerationJob).where(GenerationJob.created < now - 86400)
            )
            await db.execute(
                delete(GenerationEvent).where(GenerationEvent.created < now - 86400)
            )
            await db.commit()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
