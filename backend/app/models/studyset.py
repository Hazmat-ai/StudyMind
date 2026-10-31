import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, JSON, ForeignKey, DateTime, Uuid, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from .user import now


class QuestionType(str, enum.Enum):
    short_answer = "short_answer"
    multiple_choice = "multiple_choice"


class StudySet(Base):
    __tablename__ = "study_sets"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    generation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, unique=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    source_text: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text)
    concepts: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )
    flashcards = relationship(
        "Flashcard",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Flashcard.order_index",
        lazy="selectin",
    )
    questions = relationship(
        "Question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Question.order_index",
        lazy="selectin",
    )


class Flashcard(Base):
    __tablename__ = "flashcards"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    study_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("study_sets.id", ondelete="CASCADE"), index=True
    )
    term: Mapped[str] = mapped_column(String(255))
    definition: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    study_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("study_sets.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(32))
    options: Mapped[list] = mapped_column(JSON, default=list)
    order_index: Mapped[int] = mapped_column(Integer)
