#! /usr/bin/env bash
set -e

# Start Celery worker
celery -A app.celery.celery worker -l info &

# Start Celery beat
celery -A app.celery.celery beat -l info &

# Start FastAPI
fastapi run app/main.py --workers 4
