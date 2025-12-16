import logging
from datetime import datetime, timezone

from celery.exceptions import Ignore
from celery.signals import (
    task_failure,
    task_postrun,
    task_prerun,
    task_received,
    task_retry,
    task_revoked,
    task_success,
)
from sqlmodel import Session, select

from app.core.database import engine
from app.model.task import Task, TaskStatus
from app.model.task_execution import TaskExecution, TaskExecutionStatus

logger = logging.getLogger(__name__)


@task_received.connect
def task_received_handler(request=None, **kwargs):  # noqa: ARG001
    """
    Handler for task_received signal.
    """
    task_id = request.id if request else None
    logger.info(f"Signal task_received received for task_id: {task_id}")


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, *args, **kwargs):  # noqa: ARG001
    """
    Handler for task_prerun signal.
    """
    logger.info(
        f"Signal task_prerun received for task_id: {task_id}, task_name: {task.name if task else 'None'}"
    )
    try:
        with Session(engine) as session:
            db_task = None

            # Try to get task ID from headers (injected by beat schedule)
            if (
                task.request
                and hasattr(task.request, "headers")
                and task.request.headers
            ):
                db_task_id = task.request.headers.get("__db_task_id")
                if db_task_id:
                    logger.info(f"Found __db_task_id in headers: {db_task_id}")
                    db_task = session.get(Task, db_task_id)

            # Fallback to name matching if no ID in headers
            if not db_task:
                logger.info(
                    f"No __db_task_id in headers, falling back to name matching for: {task.name}"
                )
                statement = select(Task).where(Task.celery_task_name == task.name)
                db_task = session.exec(statement).first()

            # Update execution record if task is found
            if db_task:
                if not db_task.enabled:
                    logger.info(
                        f"Task ({db_task.name}) is disabled. Skipping execution."
                    )
                    execution = TaskExecution(
                        task_id=db_task.id,
                        task_name=db_task.name,
                        celery_task_id=task_id,
                        celery_task_args=db_task.celery_task_args,
                        celery_task_kwargs=db_task.celery_task_kwargs,
                        status=TaskExecutionStatus.DISABLED,
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                        result="Task is disabled",
                        worker=task.request.hostname if task and task.request else None,
                        runtime=0.0,
                    )
                    session.add(execution)
                    session.commit()
                    raise Ignore()
                else:
                    logger.info(
                        f"Creating new task execution record for task: {db_task.name}"
                    )
                    execution = TaskExecution(
                        task_id=db_task.id,
                        task_name=db_task.name,
                        celery_task_id=task_id,
                        celery_task_args=db_task.celery_task_args,
                        celery_task_kwargs=db_task.celery_task_kwargs,
                        status=TaskExecutionStatus.STARTED,
                        started_at=datetime.now(timezone.utc),
                        worker=task.request.hostname if task and task.request else None,
                    )
                    session.add(execution)

                    # Update Task status
                    db_task.status = TaskStatus.STARTED
                    db_task.last_run_time = datetime.now(timezone.utc)
                    db_task.celery_task_id = task_id
                    session.add(db_task)

                    session.commit()
                    return
            else:
                logger.info(
                    f"Task not found for celery task name: {task.name}. Skipping execution tracking."
                )
    except Exception as e:
        logger.error(f"Error updating task execution status to started: {e}")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):  # noqa: ARG001
    """
    Handler for task_success signal.
    """
    task_id = sender.request.id
    logger.info(f"Signal task_success received for task_id: {task_id}")
    try:
        with Session(engine) as session:
            # Find the execution record
            statement = select(TaskExecution).where(
                TaskExecution.celery_task_id == task_id
            )
            execution = session.exec(statement).first()

            if execution:
                # Update execution record to success
                logger.info(
                    f"Updating execution status to SUCCESS for task_id: {task_id}"
                )
                execution.status = TaskExecutionStatus.SUCCESS
                execution.completed_at = datetime.now(timezone.utc)
                if execution.started_at:
                    started_at = execution.started_at
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=timezone.utc)

                    completed_at = execution.completed_at
                    if completed_at.tzinfo is None:
                        completed_at = completed_at.replace(tzinfo=timezone.utc)

                    execution.runtime = (completed_at - started_at).total_seconds()
                execution.result = str(result)
                session.add(execution)

                # Update Task status
                db_task = session.get(Task, execution.task_id)
                if db_task:
                    db_task.status = TaskStatus.SUCCESS
                    session.add(db_task)

                session.commit()
            else:
                logger.debug(
                    f"No execution record found for success signal, task_id: {task_id}"
                )
    except Exception as e:
        logger.error(f"Error updating task execution status to success: {e}")


@task_failure.connect
def task_failure_handler(
    task_id=None,
    exception=None,
    traceback=None,
    einfo=None,
    *args,
    **kwargs,  # noqa: ARG001
):
    """
    Handler for task_failure signal.
    """
    if isinstance(exception, Ignore):
        logger.info(f"Task {task_id} was ignored/revoked. Skipping failure handler.")
        return

    logger.error(
        f"Signal task_failure received for task_id: {task_id}, exception: {exception}"
    )
    try:
        with Session(engine) as session:
            # Find the execution record
            statement = select(TaskExecution).where(
                TaskExecution.celery_task_id == task_id
            )
            execution = session.exec(statement).first()

            if execution:
                # Update execution record to failed
                logger.info(
                    f"Updating execution status to FAILED for task_id: {task_id}"
                )
                execution.status = TaskExecutionStatus.FAILED
                execution.completed_at = datetime.now(timezone.utc)
                if execution.started_at:
                    started_at = execution.started_at
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=timezone.utc)

                    completed_at = execution.completed_at
                    if completed_at.tzinfo is None:
                        completed_at = completed_at.replace(tzinfo=timezone.utc)

                    execution.runtime = (completed_at - started_at).total_seconds()
                execution.result = str(exception)
                execution.traceback = str(traceback)
                session.add(execution)

                # Update Task status
                db_task = session.get(Task, execution.task_id)
                if db_task:
                    db_task.status = TaskStatus.FAILED
                    session.add(db_task)

                session.commit()
            else:
                logger.debug(
                    f"No execution record found for failure signal, task_id: {task_id}"
                )
    except Exception as e:
        logger.error(f"Error updating task execution status to failure: {e}")


@task_retry.connect
def task_retry_handler(request=None, reason=None, einfo=None, **kwargs):  # noqa: ARG001
    """
    Handler for task_retry signal.
    """
    task_id = request.id if request else None
    logger.info(f"Signal task_retry received for task_id: {task_id}, reason: {reason}")
    try:
        with Session(engine) as session:
            # Find the execution record
            statement = select(TaskExecution).where(
                TaskExecution.celery_task_id == task_id
            )
            execution = session.exec(statement).first()

            if execution:
                # Update execution record to retrying
                logger.info(
                    f"Updating execution status to RETRYING for task_id: {task_id}"
                )
                execution.status = TaskExecutionStatus.RETRYING
                execution.result = str(reason)
                session.add(execution)
                session.commit()
            else:
                logger.debug(
                    f"No execution record found for retry signal, task_id: {task_id}"
                )
    except Exception as e:
        logger.error(f"Error updating task execution status to retry: {e}")


@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, retval=None, *args, **kwargs):  # noqa: ARG001
    """
    Handler for task_postrun signal.
    """
    logger.info(f"Signal task_postrun received for task_id: {task_id}")


@task_revoked.connect
def task_revoked_handler(
    request=None,
    terminated=None,
    signum=None,
    expired=None,
    **kwargs,  # noqa: ARG001
):
    """
    Handler for task_revoked signal.
    """
    task_id = request.id if request else None
    logger.info(f"Signal task_revoked received for task_id: {task_id}")
    try:
        with Session(engine) as session:
            # Find the execution record
            statement = select(TaskExecution).where(
                TaskExecution.celery_task_id == task_id
            )
            execution = session.exec(statement).first()

            if execution:
                # Update execution record to revoked
                logger.info(
                    f"Updating execution status to REVOKED for task_id: {task_id}"
                )
                execution.status = TaskExecutionStatus.REVOKED
                execution.completed_at = datetime.now(timezone.utc)
                execution.result = "Task was revoked"
                if terminated:
                    execution.result += f" (terminated, signum: {signum})"
                if expired:
                    execution.result += " (expired)"
                session.add(execution)

                # Update Task status
                db_task = session.get(Task, execution.task_id)
                if db_task:
                    db_task.status = TaskStatus.REVOKED
                    session.add(db_task)

                session.commit()
            else:
                logger.debug(
                    f"No execution record found for revoked signal, task_id: {task_id}"
                )
    except Exception as e:
        logger.error(f"Error updating task execution status to revoked: {e}")
