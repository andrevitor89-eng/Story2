from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class BookStatus(str, enum.Enum):
    draft = "draft"
    queued = "queued"
    generating = "generating"
    ready = "ready"
    failed = "failed"


class AssetKind(str, enum.Enum):
    photo = "photo"
    character = "character"
    page = "page"
    pdf = "pdf"
    video = "video"
    storyboard = "storyboard"
    narrated_video = "narrated_video"
    audio = "audio"


class JobKind(str, enum.Enum):
    GENERATE = "GENERATE"
    VIDEO = "VIDEO"
    NARRATED_VIDEO = "NARRATED_VIDEO"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    books: Mapped[list["Book"]] = relationship(back_populates="owner")
    voices: Mapped[list["UserVoice"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class UserVoice(Base):
    """Voz clonada (ElevenLabs IVC) reutilizável pelo usuário."""

    __tablename__ = "user_voices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    elevenlabs_voice_id: Mapped[str] = mapped_column(String(64))
    sample_storage_key: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(100), default="audio/mpeg")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="voices")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    child_name: Mapped[str] = mapped_column(String(80))
    child_age: Mapped[int] = mapped_column(Integer)
    child_gender: Mapped[str] = mapped_column(String(20))
    story_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    age_band: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[BookStatus] = mapped_column(Enum(BookStatus), default=BookStatus.draft)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    progress_message: Mapped[str] = mapped_column(String(255), default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrated_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="books")
    assets: Mapped[list["Asset"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    kind: Mapped[AssetKind] = mapped_column(Enum(AssetKind))
    storage_key: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(100), default="image/png")
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    book: Mapped[Book] = relationship(back_populates="assets")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    kind: Mapped[JobKind] = mapped_column(Enum(JobKind), default=JobKind.GENERATE, index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    book: Mapped[Book] = relationship(back_populates="jobs")


class StorageObject(Base):
    """Persistent blob in Postgres (optional storage backend)."""

    __tablename__ = "storage_objects"

    key: Mapped[str] = mapped_column(String(512), primary_key=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
