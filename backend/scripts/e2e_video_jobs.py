"""Enqueue and wait for video jobs on an existing ready book."""
from __future__ import annotations

import sys
import time
import uuid

from app.db import SessionLocal
from app.models import Book, JobKind, JobStatus
from app.services.jobs import enqueue_video

BOOK_ID = uuid.UUID(sys.argv[1] if len(sys.argv) > 1 else "e7a71379-fd31-4128-85b7-4b0d2ec13d47")


def wait_book(db, pred, label: str, timeout_s: int = 600, interval_s: float = 3.0) -> Book:
    deadline = time.time() + timeout_s
    n = 0
    while time.time() < deadline:
        db.expire_all()
        book = db.get(Book, BOOK_ID)
        if book is None:
            raise SystemExit(f"book {BOOK_ID} not found")
        print(f"{label} {n}: status={book.status} video={book.video_url} narr={book.narrated_video_url} msg={book.progress_message}")
        if pred(book):
            return book
        time.sleep(interval_s)
        n += 1
    raise SystemExit(f"timeout waiting for {label}")


def main() -> None:
    db = SessionLocal()
    try:
        book = wait_book(db, lambda b: b.status.value == "ready", "ebook", timeout_s=600, interval_s=5)
        print("BOOK READY")

        job = enqueue_video(db, book, kind=JobKind.VIDEO)
        print("video_job", job.id, job.kind, job.status)
        book = wait_book(db, lambda b: bool(b.video_url), "anim", timeout_s=180, interval_s=3)
        print("ANIM OK", book.video_url)

        job2 = enqueue_video(db, book, kind=JobKind.NARRATED_VIDEO)
        print("narrated_job", job2.id, job2.kind, job2.status)
        book = wait_book(db, lambda b: bool(b.narrated_video_url), "narr", timeout_s=900, interval_s=5)
        print("SUCCESS", book.video_url, book.narrated_video_url)
    finally:
        db.close()


if __name__ == "__main__":
    main()
