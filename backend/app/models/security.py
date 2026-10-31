import uuid
from sqlalchemy import ForeignKey, String, Integer, Uuid, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires: Mapped[int] = mapped_column(Integer, index=True)


class AccountToken(Base):
    __tablename__ = "account_tokens"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16))
    expires: Mapped[int] = mapped_column(Integer, index=True)


class RateLimit(Base):
    __tablename__ = "rate_limits"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    window_end: Mapped[int] = mapped_column(Integer, index=True)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    __table_args__ = (
        UniqueConstraint("user_id", "request_key", name="uq_generation_request"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    request_key: Mapped[str] = mapped_column(String(80))
    payload_hash: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16))
    created: Mapped[int] = mapped_column(Integer, index=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class GenerationQuota(Base):
    __tablename__ = "generation_quota"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)


class GenerationEvent(Base):
    """Anonymous cost reservation; account deletion must not reset the global budget."""

    __tablename__ = "generation_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created: Mapped[int] = mapped_column(Integer, index=True)
