#! /usr/bin/env bash
set -e

# Start Celery worker
celery -A app.worker.celery worker -l info &

# Start Celery beat
celery -A app.worker.celery beat -l info &

# Start FastAPI with reload
fastapi run app/main.py --workers 4 --reload
