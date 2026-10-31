import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    study_sets = relationship(
        "StudySet", cascade="all, delete-orphan", passive_deletes=True
    )
