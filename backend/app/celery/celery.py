from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URI,
    backend=settings.REDIS_URI,
    include=["app.celery.tasks", "app.celery.handlers"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60,  # 60 minutes
    task_soft_time_limit=55 * 60,  # 55 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=4,
    beat_scheduler="app.celery.scheduler.DatabaseScheduler",
)
