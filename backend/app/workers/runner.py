from __future__ import annotations

import asyncio
import logging
import time

import redis

from app.config import settings
from app.db import SessionLocal
from app.services.jobs import REDIS_CHANNEL, claim_next_job, mark_job_done, mark_job_failed
from app.workers.handlers import process_generate_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("worker")


def _wait_for_wake(timeout: float = 5.0) -> None:
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.blpop(REDIS_CHANNEL, timeout=int(timeout))
        client.close()
    except Exception:  # noqa: BLE001
        time.sleep(timeout)


async def run_once() -> bool:
    db = SessionLocal()
    try:
        job = claim_next_job(db)
        if job is None:
            return False
        logger.info("Processing job %s for book %s", job.id, job.book_id)
        try:
            await process_generate_job(db, job)
            mark_job_done(db, job)
            logger.info("Job %s completed", job.id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Job %s failed", job.id)
            mark_job_failed(db, job, str(exc))
        return True
    finally:
        db.close()


async def main() -> None:
    logger.info("Worker started (offline_fallback=%s, has_gemini=%s)",
                settings.offline_fallback, bool(settings.gemini_api_key))
    while True:
        worked = await run_once()
        if not worked:
            await asyncio.to_thread(_wait_for_wake, 5.0)


if __name__ == "__main__":
    asyncio.run(main())
