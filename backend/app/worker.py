"""
Celery worker entry point.
This module initializes the Celery application and imports all tasks.
"""
import logging

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URI,
    backend=settings.REDIS_URI,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=4,
)

# Import all tasks to register them
from app.api.tasks import (  # noqa: E402
    demo_async_task,
    demo_dynamic_task,
    demo_periodic_task,
    demo_scheduled_task,
)

# Import celery handlers to register signals
logger.info("Importing celery handlers...")
import app.core.celery_handlers  # noqa: F401, E402
logger.info("Celery handlers imported.")

# Configure periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    "demo-periodic-task": {
        "task": "app.api.tasks.demo_periodic_task",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}

# Load periodic tasks from database
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Load periodic tasks from database on Celery startup
    """
    try:
        from sqlmodel import Session, select
        from app.core.database import engine
        from app.model.task import Task, TaskType, PeriodicScheduleType, TaskStatus
        from celery.schedules import crontab, schedule
        from datetime import timedelta
        import json

        logger.info("Loading periodic tasks from database...")
        
        with Session(engine) as session:
            # Query enabled periodic tasks
            statement = select(Task).where(
                Task.task_type == TaskType.PERIODIC,
                Task.enabled == True,
                Task.status != TaskStatus.DISABLED
            )
            tasks = session.exec(statement).all()
            
            for task in tasks:
                try:
                    logger.info(f"Registering periodic task: {task.name}")
                    
                    # Parse args/kwargs
                    args = json.loads(task.task_args) if task.task_args else []
                    kwargs = json.loads(task.task_kwargs) if task.task_kwargs else {}
                    
                    task_schedule = None
                    if task.periodic_schedule_type == PeriodicScheduleType.CRONTAB:
                        task_schedule = crontab(
                            minute=task.crontab_minute or "*",
                            hour=task.crontab_hour or "*",
                            day_of_week=task.crontab_day_of_week or "*",
                            day_of_month=task.crontab_day_of_month or "*",
                            month_of_year=task.crontab_month_of_year or "*",
                        )
                    elif task.periodic_schedule_type == PeriodicScheduleType.INTERVAL:
                        seconds = task.interval_seconds or 0
                        minutes = task.interval_minutes or 0
                        hours = task.interval_hours or 0
                        days = task.interval_days or 0
                        
                        if any([seconds, minutes, hours, days]):
                            task_schedule = schedule(
                                run_every=timedelta(
                                    days=days,
                                    hours=hours,
                                    minutes=minutes,
                                    seconds=seconds
                                )
                            )
                    
                    if task_schedule:
                        # Update beat_schedule directly
                        sender.conf.beat_schedule[task.name] = {
                            "task": task.celery_task_name,
                            "schedule": task_schedule,
                            "args": args,
                            "kwargs": kwargs,
                            "options": {"headers": {"__task_db_id": str(task.id)}}
                        }
                        logger.info(f"Successfully registered task: {task.name}")
                    else:
                        logger.warning(f"Skipping task {task.name}: Invalid schedule configuration")
                except Exception as e:
                    logger.error(f"Error registering task {task.name}: {e}")
                    
    except Exception as e:
        logger.error(f"Error loading periodic tasks: {e}")

logger.info("Celery worker initialized successfully")
