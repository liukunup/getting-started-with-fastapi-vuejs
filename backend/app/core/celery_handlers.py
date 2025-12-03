import logging
import sys
from datetime import datetime

print("Loading app.core.celery_handlers module...", file=sys.stderr)

from celery.signals import task_failure, task_prerun, task_success
from celery.exceptions import Ignore
from sqlmodel import Session, select

from app.core.database import engine
from app.model.task import Task, TaskStatus
from app.model.task_execution import TaskExecution

logger = logging.getLogger(__name__)
# Ensure logs are shown in stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, *args, **kwargs):
    """
    Handler for task_prerun signal.
    Updates the task execution status to 'running'.
    """
    logger.info(f"Signal task_prerun received for task_id: {task_id}, task_name: {task.name if task else 'None'}")
    try:
        with Session(engine) as session:
            statement = select(TaskExecution).where(TaskExecution.celery_task_id == task_id)
            execution = session.exec(statement).first()
            
            if not execution and task:
                logger.info(f"No existing execution found for task_id: {task_id}. Searching for task definition: {task.name}")
                # Try to find the task definition in DB to create a new execution record
                # This handles periodic tasks or tasks not triggered via API
                
                db_task = None
                # Try to get task ID from headers (injected by beat schedule)
                if task.request and hasattr(task.request, "headers") and task.request.headers:
                    task_db_id = task.request.headers.get("__task_db_id")
                    if task_db_id:
                        logger.info(f"Found task DB ID in headers: {task_db_id}")
                        db_task = session.get(Task, task_db_id)

                # Fallback to name matching if no ID in headers
                if not db_task:
                    logger.info(f"No task DB ID in headers, falling back to name matching for: {task.name}")
                    task_statement = select(Task).where(Task.celery_task_name == task.name)
                    db_task = session.exec(task_statement).first()
                
                if db_task:
                    if not db_task.enabled or db_task.status == TaskStatus.DISABLED:
                        logger.info(f"Task {db_task.name} is disabled. Skipping execution.")
                        execution = TaskExecution(
                            task_id=db_task.id,
                            task_name=db_task.name,
                            celery_task_id=task_id,
                            status="revoked",
                            started_at=datetime.utcnow(),
                            completed_at=datetime.utcnow(),
                            result="Task is disabled",
                            worker=task.request.hostname if task and task.request else None
                        )
                        session.add(execution)
                        session.commit()
                        raise Ignore()

                    logger.info(f"Creating new execution record for task: {db_task.name}")
                    execution = TaskExecution(
                        task_id=db_task.id,
                        task_name=db_task.name,
                        celery_task_id=task_id,
                        status="running",
                        started_at=datetime.utcnow(),
                        args=str(args) if args else None,
                        kwargs=str(kwargs) if kwargs else None,
                        worker=task.request.hostname if task and task.request else None
                    )
                    session.add(execution)
                    
                    # Update Task status
                    db_task.status = "running"
                    session.add(db_task)
                    
                    session.commit()
                    return
                else:
                    logger.info(f"Task definition not found for celery task name: {task.name}. Skipping execution tracking.")

            if execution:
                # Check if task is disabled
                task_record = session.get(Task, execution.task_id)
                if task_record and (not task_record.enabled or task_record.status == TaskStatus.DISABLED):
                    logger.info(f"Task {task_record.name} is disabled. Aborting execution.")
                    execution.status = "revoked"
                    execution.result = "Task is disabled"
                    execution.completed_at = datetime.utcnow()
                    session.add(execution)
                    session.commit()
                    raise Ignore()

                logger.info(f"Updating execution status to running for task_id: {task_id}")
                execution.status = "running"
                execution.started_at = datetime.utcnow()
                if task and task.request and task.request.hostname:
                    execution.worker = task.request.hostname
                session.add(execution)
                
                # Update Task status
                task_record = session.get(Task, execution.task_id)
                if task_record:
                    task_record.status = "running"
                    session.add(task_record)
                
                session.commit()
    except Exception as e:
        logger.error(f"Error updating task execution status to running: {e}")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """
    Handler for task_success signal.
    Updates the task execution status to 'success'.
    """
    task_id = sender.request.id
    logger.info(f"Signal task_success received for task_id: {task_id}")
    try:
        with Session(engine) as session:
            statement = select(TaskExecution).where(TaskExecution.celery_task_id == task_id)
            execution = session.exec(statement).first()
            if execution:
                logger.info(f"Updating execution status to success for task_id: {task_id}")
                execution.status = "success"
                execution.completed_at = datetime.utcnow()
                if execution.started_at:
                    execution.runtime = (execution.completed_at - execution.started_at).total_seconds()
                execution.result = str(result)
                session.add(execution)
                
                # Update Task status
                task_record = session.get(Task, execution.task_id)
                if task_record:
                    task_record.status = "success"
                    session.add(task_record)
                
                session.commit()
            else:
                logger.debug(f"No execution record found for success signal, task_id: {task_id}")
    except Exception as e:
        logger.error(f"Error updating task execution status to success: {e}")


@task_failure.connect
def task_failure_handler(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **kw,
):
    """
    Handler for task_failure signal.
    Updates the task execution status to 'failure'.
    """
    if isinstance(exception, Ignore):
        logger.info(f"Task {task_id} was ignored/revoked. Skipping failure handler.")
        return

    logger.error(f"Signal task_failure received for task_id: {task_id}, exception: {exception}")
    try:
        with Session(engine) as session:
            statement = select(TaskExecution).where(TaskExecution.celery_task_id == task_id)
            execution = session.exec(statement).first()
            if execution:
                logger.info(f"Updating execution status to failure for task_id: {task_id}")
                execution.status = "failure"
                execution.completed_at = datetime.utcnow()
                if execution.started_at:
                    execution.runtime = (execution.completed_at - execution.started_at).total_seconds()
                execution.result = str(exception)
                execution.traceback = str(traceback)
                session.add(execution)
                
                # Update Task status
                task_record = session.get(Task, execution.task_id)
                if task_record:
                    task_record.status = "failed"
                    session.add(task_record)
                
                session.commit()
            else:
                logger.debug(f"No execution record found for failure signal, task_id: {task_id}")
    except Exception as e:
        logger.error(f"Error updating task execution status to failure: {e}")
