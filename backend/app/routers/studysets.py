import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models import User, StudySet, Flashcard, Question, GenerationJob
from ..schemas.generate import StudyMaterial
from ..schemas.studyset import (
    StudySetCreate,
    RenameStudySet,
    StudySetDisplay,
    StudySetPage,
    StudySetExport,
)
from ..security import get_current_user

router = APIRouter()


def serialize(item, full=True):
    data = {
        "id": str(item.id),
        "title": item.title,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }
    if full:
        data.update(
            source_text=item.source_text,
            summary=item.summary,
            concepts=item.concepts,
            flashcards=[
                {"term": c.term, "definition": c.definition} for c in item.flashcards
            ],
            questions=[
                {
                    "question": q.question,
                    "answer": q.answer,
                    "type": q.question_type,
                    "options": q.options,
                }
                for q in item.questions
            ],
        )
    return data


async def owned(db, user_id, item_id):
    item = await db.scalar(
        select(StudySet).where(StudySet.id == item_id, StudySet.user_id == user_id)
    )
    if item is None:
        raise HTTPException(404, "Study set not found")
    return item


@router.post("", status_code=201, response_model=StudySetDisplay)
async def save(
    data: StudySetCreate,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.id
    await db.scalar(select(User).where(User.id == user_id).with_for_update())
    existing = await db.scalar(
        select(StudySet).where(
            StudySet.generation_id == data.generation_id, StudySet.user_id == user_id
        )
    )
    if existing:
        response.status_code = 200
        return serialize(existing)
    count = await db.scalar(
        select(func.count()).select_from(StudySet).where(StudySet.user_id == user_id)
    )
    if count >= 100:
        raise HTTPException(
            409, "You have 100 saved sets. Export or delete an older set first."
        )
    job = await db.scalar(
        select(GenerationJob).where(
            GenerationJob.id == data.generation_id, GenerationJob.user_id == user_id
        )
    )
    if (
        job is None
        or job.state != "completed"
        or job.result is None
        or job.created < __import__("time").time() - 3600
    ):
        raise HTTPException(404, "This draft expired or is unavailable")
    material = StudyMaterial.model_validate(job.result)
    item = StudySet(
        user_id=user_id,
        generation_id=job.id,
        title=data.title or material.title,
        source_text=data.source_text,
        summary=material.summary,
        concepts=[c.model_dump() for c in material.concepts],
    )
    item.flashcards = [
        Flashcard(term=c.term, definition=c.definition, order_index=i)
        for i, c in enumerate(material.flashcards)
    ]
    item.questions = [
        Question(
            question=q.question,
            answer=q.answer,
            question_type=q.type,
            options=q.options,
            order_index=i,
        )
        for i, q in enumerate(material.questions)
    ]
    db.add(item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(
            select(StudySet).where(
                StudySet.generation_id == data.generation_id,
                StudySet.user_id == user_id,
            )
        )
        if existing:
            response.status_code = 200
            return serialize(existing)
        raise HTTPException(409, "Could not save this draft. Please retry.")
    return serialize(item)


@router.get("", response_model=StudySetPage)
async def list_sets(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(
        select(func.count()).select_from(StudySet).where(StudySet.user_id == user.id)
    )
    items = (
        await db.scalars(
            select(StudySet)
            .where(StudySet.user_id == user.id)
            .order_by(StudySet.created_at.desc(), StudySet.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return {"items": [serialize(i, False) for i in items], "total": total}


@router.get("/export", response_model=StudySetExport)
async def export(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    items = (
        await db.scalars(
            select(StudySet)
            .where(StudySet.user_id == user.id)
            .order_by(StudySet.created_at)
        )
    ).all()
    return {"version": 1, "sets": [serialize(i) for i in items]}


@router.get("/{item_id}", response_model=StudySetDisplay)
async def get(
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return serialize(await owned(db, user.id, item_id))


@router.patch("/{item_id}", response_model=StudySetDisplay)
async def rename(
    item_id: uuid.UUID,
    data: RenameStudySet,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await owned(db, user.id, item_id)
    item.title = data.title
    await db.commit()
    return serialize(item)


@router.delete("/{item_id}", status_code=204)
async def delete(
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await owned(db, user.id, item_id)
    await db.delete(item)
    await db.commit()
    return Response(status_code=204)
