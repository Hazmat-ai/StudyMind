import uuid
from pydantic import Field
from .auth import StrictModel


class StudySetCreate(StrictModel):
    generation_id: uuid.UUID
    title: str | None = Field(default=None, min_length=1, max_length=255)
    source_text: str = Field(default="", max_length=12000)


class RenameStudySet(StrictModel):
    title: str = Field(min_length=1, max_length=255)


from datetime import datetime
from .generate import GeneratedFlashcard, GeneratedQuestion, GeneratedConcept


class StudySetListDisplay(StrictModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class StudySetDisplay(StudySetListDisplay):
    source_text: str
    summary: str
    flashcards: list[GeneratedFlashcard]
    questions: list[GeneratedQuestion]
    concepts: list[GeneratedConcept]


class StudySetPage(StrictModel):
    items: list[StudySetListDisplay]
    total: int


class StudySetExport(StrictModel):
    version: int
    sets: list[StudySetDisplay]
