#!/bin/sh
set -e
alembic upgrade head
python -m app.workers.runner &
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
