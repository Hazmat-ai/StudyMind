import asyncio
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from app.config import Settings
from app.database import Base
from app import models  # noqa: F401 -- registers all mapped tables with Base.metadata

config = context.config
settings = Settings()
target_metadata = Base.metadata


def offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def sync_migrations(connection):
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def online():
    engine = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(sync_migrations)
    await engine.dispose()


if context.is_offline_mode():
    offline()
else:
    asyncio.run(online())
