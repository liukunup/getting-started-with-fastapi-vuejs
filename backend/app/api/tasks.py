import logging

from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(acks_late=True)
def demo_async_task():
    """
    A demo async task.
    """
    import time

    # Simulate a long-running task
    time.sleep(10)

    return "Task completed"


@celery_app.task(acks_late=True)
def demo_periodic_task():
    """
    A demo periodic task.
    """

    # Simulate periodic task work
    logger.info("Periodic task executed")

    return "Periodic task completed"


@celery_app.task(acks_late=True)
def demo_scheduled_task():
    """
    A demo scheduled task.
    """

    # Simulate scheduled task work
    logger.info("Scheduled task executed")

    return "Scheduled task completed"


@celery_app.task(bind=True, acks_late=True)
def demo_dynamic_task(self, *args, **kwargs):
    """
    A demo dynamic task that accepts arguments.
    """
    logger.info(f"Dynamic task executed with args: {args}, kwargs: {kwargs}")
    return f"Dynamic task completed with args: {args}, kwargs: {kwargs}"


@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(acks_late=True)
def long_running_task(seconds: int) -> str:
    import time

    time.sleep(seconds)
    return f"long running task finished in {seconds}s"
