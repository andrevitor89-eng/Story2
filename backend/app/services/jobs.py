from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Book, BookStatus, Job, JobKind, JobStatus

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
    job = Job(book_id=book.id, kind=JobKind.GENERATE, status=JobStatus.queued)
    book.status = BookStatus.queued
    book.progress = 0
    book.progress_message = "Na fila..."
    book.error_message = None
    book.video_url = None
    book.narrated_video_url = None
    db.add(job)
    db.commit()
    db.refresh(job)
    notify_workers()
    return job


def enqueue_video(
    db: Session,
    book: Book,
    *,
    kind: JobKind = JobKind.VIDEO,
    payload: dict[str, Any] | None = None,
) -> Job:
    """Enfileira Animação (VIDEO) ou vídeo narrado (NARRATED_VIDEO) sem alterar status do ebook."""
    if kind not in (JobKind.VIDEO, JobKind.NARRATED_VIDEO):
        raise ValueError(f"kind inválido para vídeo: {kind}")
    # Evita fila duplicada do mesmo tipo
    active = next(
        (
            j
            for j in book.jobs
            if j.kind == kind and j.status in (JobStatus.queued, JobStatus.running)
        ),
        None,
    )
    if active:
        return active
    job = Job(
        book_id=book.id,
        kind=kind,
        status=JobStatus.queued,
        payload=json.dumps(payload) if payload else None,
    )
    book.progress_message = (
        "Animação na fila..." if kind == JobKind.VIDEO else "Vídeo narrado na fila..."
    )
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
    if book and job.kind == JobKind.GENERATE:
        book.status = BookStatus.generating
        book.progress_message = "Gerando..."
    elif book and job.kind == JobKind.VIDEO:
        book.progress_message = "Gerando animação..."
    elif book and job.kind == JobKind.NARRATED_VIDEO:
        book.progress_message = "Montando vídeo narrado..."
    db.commit()
    db.refresh(job)
    return job


def mark_job_done(db: Session, job: Job) -> None:
    job.status = JobStatus.completed
    job.finished_at = datetime.now(timezone.utc)
    book = db.get(Book, job.book_id)
    if book:
        if job.kind == JobKind.GENERATE:
            book.status = BookStatus.ready
            book.progress = 100
            book.progress_message = "Pronto!"
        else:
            # Mantém ebook ready; só atualiza mensagem
            if book.status == BookStatus.ready:
                book.progress_message = "Pronto!"
            elif job.kind == JobKind.VIDEO:
                book.progress_message = "Animação pronta!"
            else:
                book.progress_message = "Vídeo narrado pronto!"
    db.commit()


def mark_job_failed(db: Session, job: Job, message: str) -> None:
    job.status = JobStatus.failed
    job.error_message = message[:2000]
    job.finished_at = datetime.now(timezone.utc)
    book = db.get(Book, job.book_id)
    if book:
        if job.kind == JobKind.GENERATE:
            book.status = BookStatus.failed
            book.error_message = message[:2000]
            book.progress_message = "Falhou"
        else:
            book.progress_message = (
                "Falha na animação" if job.kind == JobKind.VIDEO else "Falha no vídeo narrado"
            )
            book.error_message = message[:2000]
    db.commit()
