import asyncio
import time
import uuid
from sqlalchemy import update, select, func
from app import maintenance
from app.models import GenerationJob, GenerationEvent
from conftest import login
from test_generation import generate


def test_expired_drafts_purged_without_losing_saved_material_or_current_budget(
    client, application, monkeypatch
):
    auth = login(client)
    draft = generate(client, auth).json()["generation_id"]
    saved = client.post(
        "/api/studysets", headers=auth, json={"generation_id": draft}
    ).json()["id"]

    async def expire():
        async with application.state.sessions() as db:
            await db.execute(
                update(GenerationJob)
                .where(GenerationJob.id == uuid.UUID(draft))
                .values(created=int(time.time()) - 90000)
            )
            db.add(GenerationEvent(created=int(time.time()) - 90000))
            await db.commit()

    client.portal.call(expire)
    monkeypatch.setattr(maintenance, "Settings", lambda: application.state.settings)
    asyncio.run(maintenance.main())
    assert client.get("/api/generate/" + draft, headers=auth).status_code == 404
    assert client.get("/api/studysets/" + saved, headers=auth).status_code == 200

    async def remaining():
        async with application.state.sessions() as db:
            return await db.scalar(select(func.count()).select_from(GenerationEvent))

    assert client.portal.call(remaining) == 1
