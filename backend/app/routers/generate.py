import asyncio
import hmac
import hashlib
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Header, File, UploadFile
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User, GenerationJob, GenerationQuota, GenerationEvent
from ..security import get_current_user, settings, rate_limit
from ..schemas.generate import GenerateRequest, GenerateResponse, StudyMaterial
from ..services.ai import generate_study_set
from ..services.pdf import extract_text_from_pdf

router = APIRouter()


def get_generator():
    return generate_study_set


def reply(job):
    if (
        job.state == "completed"
        and job.result
        and job.created > int(time.time()) - 3600
    ):
        return GenerateResponse(**job.result, generation_id=job.id)
    if job.state == "pending" and job.created > int(time.time()) - 180:
        raise HTTPException(
            409,
            "This generation is still running. Wait a moment and retry.",
            headers={"Retry-After": "3"},
        )
    if job.state == "completed":
        raise HTTPException(410, "This unsaved draft expired. Create a new generation.")
    raise HTTPException(503, "This generation failed. Start a new attempt to retry.")


@router.post("", response_model=GenerateResponse)
async def generate(
    data: GenerateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    generator=Depends(get_generator),
    idempotency_key: str = Header(
        min_length=16, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$"
    ),
):
    user_id = user.id
    config = settings(request)
    now = int(time.time())
    if generator is generate_study_set and (
        not config.anthropic_api_key or not config.anthropic_model
    ):
        raise HTTPException(503, "Study generation is currently unavailable")
    fingerprint = hmac.new(
        config.secret_key.encode(), data.model_dump_json().encode(), hashlib.sha256
    ).hexdigest()
    quota = await db.scalar(
        select(GenerationQuota).where(GenerationQuota.id == "global").with_for_update()
    )
    if quota is None:
        raise HTTPException(503, "Generation quota is unavailable")
    await db.scalar(select(User).where(User.id == user_id).with_for_update())
    existing = await db.scalar(
        select(GenerationJob).where(
            GenerationJob.user_id == user_id,
            GenerationJob.request_key == idempotency_key,
        )
    )
    if existing:
        if not hmac.compare_digest(existing.payload_hash, fingerprint):
            raise HTTPException(
                409,
                "This request key belongs to different content. Start a new generation.",
            )
        return reply(existing)
    await db.execute(
        update(GenerationJob)
        .where(
            GenerationJob.user_id == user_id,
            GenerationJob.state == "pending",
            GenerationJob.created <= now - 180,
        )
        .values(state="failed")
    )
    daily = await db.scalar(
        select(func.count())
        .select_from(GenerationJob)
        .where(GenerationJob.user_id == user_id, GenerationJob.created >= now - 86400)
    )
    global_daily = await db.scalar(
        select(func.count())
        .select_from(GenerationEvent)
        .where(GenerationEvent.created >= now - 86400)
    )
    active = await db.scalar(
        select(func.count())
        .select_from(GenerationJob)
        .where(GenerationJob.user_id == user_id, GenerationJob.state == "pending")
    )
    if (
        daily >= config.generation_daily_limit
        or global_daily >= config.generation_global_daily_limit
        or active >= config.generation_concurrency
    ):
        raise HTTPException(
            429,
            "Generation allowance reached. Wait before starting another request.",
            headers={"Retry-After": "60"},
        )
    job = GenerationJob(
        user_id=user_id,
        request_key=idempotency_key,
        payload_hash=fingerprint,
        state="pending",
        created=now,
    )
    db.add(job)
    db.add(GenerationEvent(created=now))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(
            select(GenerationJob).where(
                GenerationJob.user_id == user_id,
                GenerationJob.request_key == idempotency_key,
            )
        )
        if existing:
            if not hmac.compare_digest(existing.payload_hash, fingerprint):
                raise HTTPException(
                    409,
                    "This request key belongs to different content. Start a new generation.",
                )
            return reply(existing)
        raise HTTPException(409, "Another request changed this account. Retry shortly.")
    job_id = job.id
    try:
        material = await asyncio.wait_for(
            generator(data.content, data.options, config), timeout=110
        )
        # Validate even dependency-injected providers before persisting anything.
        material = StudyMaterial.model_validate(material)
        if (
            len(material.flashcards) != data.options.num_flashcards
            or len(material.questions) != data.options.num_questions
        ):
            raise ValueError("Unexpected provider counts")
        job.result = material.model_dump(mode="json")
        job.state = "completed"
        await db.commit()
        return GenerateResponse(**job.result, generation_id=job.id)
    except (Exception, asyncio.CancelledError):
        await db.rollback()
        await db.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job_id)
            .values(state="failed")
        )
        await db.commit()
        raise HTTPException(
            503,
            "AI generation is unavailable or returned invalid material. Your notes were not saved. You can start a new attempt.",
        )


@router.get("/{generation_id}", response_model=GenerateResponse)
async def draft(
    generation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.scalar(
        select(GenerationJob).where(
            GenerationJob.id == generation_id, GenerationJob.user_id == user.id
        )
    )
    if job is None:
        raise HTTPException(404, "Draft not found")
    return reply(job)


@router.post("/extract-pdf")
async def extract(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    await rate_limit(request, "pdf:" + str(user.id), 20, 3600)
    try:
        await asyncio.wait_for(request.app.state.pdf_slots.acquire(), timeout=0.05)
    except TimeoutError:
        await file.close()
        raise HTTPException(
            429, "PDF processing is busy. Retry shortly.", headers={"Retry-After": "5"}
        )
    try:
        return {"content": await extract_text_from_pdf(file)}
    finally:
        request.app.state.pdf_slots.release()
