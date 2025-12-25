import logging

from app.worker.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="demo_task", acks_late=True)
def demo_task():
    """
    A demo task.
    """
    import time

    # Simulate a long-running task
    time.sleep(10)
    logger.info("Demo task executed")

    return "Task completed"


@celery_app.task(name="demo_dynamic_task", bind=True, acks_late=True)
def demo_dynamic_task(self, *args, **kwargs):  # noqa: ARG001
    """
    A demo dynamic task that accepts arguments.
    """

    logger.info(
        f"Dynamic task {self.request.id} executed with args: {args}, kwargs: {kwargs}"
    )

    return (
        f"Dynamic task {self.request.id} completed with args: {args}, kwargs: {kwargs}"
    )
