from __future__ import annotations

import logging
from datetime import datetime, timezone

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Book, BookStatus, Job, JobStatus

logger = logging.getLogger("jobs")
REDIS_CHANNEL = "story2:jobs"


def notify_workers() -> None:
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.lpush(REDIS_CHANNEL, "wake")
        client.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis notify failed: %s", exc)


def enqueue_generate(db: Session, book: Book) -> Job:
    job = Job(book_id=book.id, status=JobStatus.queued)
    book.status = BookStatus.queued
    book.progress = 0
    book.progress_message = "Na fila..."
    book.error_message = None
    db.add(job)
    db.commit()
    db.refresh(job)
    notify_workers()
    return job


def claim_next_job(db: Session) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.status == JobStatus.queued)
        .order_by(Job.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    job = db.execute(stmt).scalar_one_or_none()
    if job is None:
        return None
    job.status = JobStatus.running
    job.started_at = datetime.now(timezone.utc)
    book = db.get(Book, job.book_id)
    if book:
        book.status = BookStatus.generating
        book.progress_message = "Gerando..."
    db.commit()
    db.refresh(job)
    return job


def mark_job_done(db: Session, job: Job) -> None:
    job.status = JobStatus.completed
    job.finished_at = datetime.now(timezone.utc)
    book = db.get(Book, job.book_id)
    if book:
        book.status = BookStatus.ready
        book.progress = 100
        book.progress_message = "Pronto!"
    db.commit()


def mark_job_failed(db: Session, job: Job, message: str) -> None:
    job.status = JobStatus.failed
    job.error_message = message[:2000]
    job.finished_at = datetime.now(timezone.utc)
    book = db.get(Book, job.book_id)
    if book:
        book.status = BookStatus.failed
        book.error_message = message[:2000]
        book.progress_message = "Falhou"
    db.commit()
