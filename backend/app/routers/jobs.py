from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Job, User
from app.schemas import JobOut
from app.security import get_current_user

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    job = db.get(Job, job_id)
    if job is None or job.book.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job nao encontrado")
    return job