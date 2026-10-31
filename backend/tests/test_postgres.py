"""Runs only against a disposable, dedicated PostgreSQL database in CI."""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, text
from app.config import Settings
from app.main import create_app
from app.models import User, RateLimit, GenerationJob, GenerationEvent
from app.routers.generate import get_generator
from conftest import CONTENT, ORIGIN, login, material


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Dedicated PostgreSQL test database not configured",
)
def test_postgres_migration_quota_lock_and_idempotency(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    url = os.environ["TEST_DATABASE_URL"]
    secret = "postgres-only-test-secret" * 3
    env = {
        **os.environ,
        "SECRET_KEY": secret,
        "DATABASE_URL": url,
        "APP_ENV": "testing",
    }
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(root / "backend/alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=root,
        env=env,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(root / "backend/alembic.ini"),
            "check",
        ],
        cwd=root,
        env=env,
        check=True,
    )
    config = Settings(
        app_env="testing",
        secret_key=secret,
        database_url=url,
        require_email_verification=False,
        generation_daily_limit=1,
        generation_global_daily_limit=1,
    )
    app = create_app(config)
    calls = []

    async def provider(content, options, settings):
        calls.append(content)
        await asyncio.sleep(0.15)
        return material(options)

    app.dependency_overrides[get_generator] = lambda: provider
    with TestClient(
        app, base_url="http://localhost:8000", headers={"Origin": ORIGIN}
    ) as client:

        async def cleanup():
            async with app.state.sessions() as db:
                await db.execute(delete(User))
                await db.execute(delete(GenerationJob))
                await db.execute(delete(GenerationEvent))
                await db.execute(delete(RateLimit))
                await db.commit()

        client.portal.call(cleanup)
        a = login(client, "pg-a@example.com")
        client.cookies.clear()
        b = login(client, "pg-b@example.com")
        body = {
            "content": CONTENT,
            "options": {
                "num_flashcards": 2,
                "num_questions": 1,
                "difficulty": "university",
            },
            "consent_to_provider": True,
        }

        def request(headers, key):
            return client.post(
                "/api/generate", json=body, headers={**headers, "Idempotency-Key": key}
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [
                pool.submit(request, a, "postgres-request-a"),
                pool.submit(request, b, "postgres-request-b"),
            ]
            results = [f.result() for f in jobs]
        assert sorted(r.status_code for r in results) == [200, 429]
        assert len(calls) == 1
        winner = a if results[0].status_code == 200 else b
        key = "postgres-request-a" if winner is a else "postgres-request-b"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: request(winner, key), range(2)))
        assert all(r.status_code == 200 for r in results)
        assert results[0].json()["generation_id"] == results[1].json()["generation_id"]
        assert len(calls) == 1
        client.portal.call(cleanup)
        calls.clear()
        a = login(client, "pg-c@example.com")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(lambda _: request(a, "same-key-pending-test"), range(2))
            )
        assert sorted(r.status_code for r in results) in ([200, 409], [200, 200])
        assert len(calls) == 1

        # Shared SQL limiter must never lose increments under concurrent connections.
        async def counts():
            from app.security import rate_limit
            from starlette.requests import Request

            request = Request({"type": "http", "app": app})
            outcomes = await asyncio.gather(
                *(rate_limit(request, "pg-atomic-limit", 3, 60) for _ in range(10)),
                return_exceptions=True,
            )
            assert sum(item is None for item in outcomes) == 3
            async with app.state.sessions() as db:
                assert (
                    await db.execute(
                        text("SELECT count FROM rate_limits WHERE count=10")
                    )
                ).scalar_one() == 10

        client.portal.call(counts)
