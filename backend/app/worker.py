from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_INDEX}",
    backend=f"db+{str(settings.SQLALCHEMY_DATABASE_URI)}",
)

celery_app.conf.task_routes = {
    "app.worker.test_celery": "main-queue",
    "app.worker.long_running_task": "main-queue",
}

celery_app.conf.beat_schedule = {
    "test-periodic-task": {
        "task": "app.worker.test_celery",
        "schedule": 60.0,  # every 60 seconds
        "args": ("periodic world",),
    },
}


@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(acks_late=True)
def long_running_task(seconds: int) -> str:
    import time

    time.sleep(seconds)
    return f"Task finished after {seconds} seconds"
