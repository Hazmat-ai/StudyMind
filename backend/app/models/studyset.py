import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Enum
from ..database import Base
from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .user import User

import enum

class QuestionType(str, enum.Enum):
    short_answer = "short_answer"
    multiple_choice = "multiple_choice"

class StudySet(Base):
    __tablename__ = "study_sets"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    concepts: Mapped[Optional[dict]] = mapped_column(JSON)

    user: Mapped["User"] = relationship("User", back_populates="study_sets")
    flashcards: Mapped[List["Flashcard"]] = relationship("Flashcard", back_populates="study_set", cascade="all, delete-orphan", order_by="Flashcard.order_index")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="study_set", cascade="all, delete-orphan", order_by="Question.order_index")

class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_set_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("study_sets.id"))
    term: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(nullable=False)

    study_set: Mapped["StudySet"] = relationship("StudySet", back_populates="flashcards")

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_set_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("study_sets.id"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    options: Mapped[Optional[dict]] = mapped_column(JSON)
    order_index: Mapped[int] = mapped_column(nullable=False)

    study_set: Mapped["StudySet"] = relationship("StudySet", back_populates="questions")
