import json
import logging
from datetime import datetime, timedelta, timezone

from celery.beat import ScheduleEntry, Scheduler
from celery.schedules import crontab, schedule
from sqlmodel import Session, select

from app.core.database import engine
from app.model.task import PeriodicScheduleType, Task, TaskType

logger = logging.getLogger(__name__)


class DatabaseScheduleEntry(ScheduleEntry):
    def __init__(self, db_task: Task, app=None):
        self.db_task = db_task

        args = json.loads(db_task.celery_task_args) if db_task.celery_task_args else []
        kwargs = (
            json.loads(db_task.celery_task_kwargs) if db_task.celery_task_kwargs else {}
        )

        schedule_obj = None

        if db_task.periodic_schedule_type == PeriodicScheduleType.CRONTAB:
            schedule_obj = crontab(
                minute=db_task.crontab_minute or "*",
                hour=db_task.crontab_hour or "*",
                day_of_week=db_task.crontab_day_of_week or "*",
                day_of_month=db_task.crontab_day_of_month or "*",
                month_of_year=db_task.crontab_month_of_year or "*",
            )

        elif db_task.periodic_schedule_type == PeriodicScheduleType.INTERVAL:
            seconds = db_task.interval_seconds or 0
            minutes = db_task.interval_minutes or 0
            hours = db_task.interval_hours or 0
            days = db_task.interval_days or 0

            if any([seconds, minutes, hours, days]):
                schedule_obj = schedule(
                    run_every=timedelta(
                        days=days,
                        hours=hours,
                        minutes=minutes,
                        seconds=seconds,
                    )
                )

        super().__init__(
            name=db_task.name,
            task=db_task.celery_task_name,
            last_run_at=db_task.last_run_time,
            total_run_count=0,
            schedule=schedule_obj,
            args=args,
            kwargs=kwargs,
            options={"headers": {"__db_task_id": str(db_task.id)}},
            app=app,
        )

    def _default_now(self):
        return self.app.now()

    def __next__(self):
        self.db_task.last_run_time = self._default_now().astimezone(timezone.utc)

        # Update last_run_time in DB
        try:
            with Session(engine) as session:
                statement = select(Task).where(Task.id == self.db_task.id)
                task = session.exec(statement).first()
                if task:
                    task.last_run_time = self.db_task.last_run_time

                    session.add(task)
                    session.commit()
        except Exception as e:
            logger.error(f"Error updating last_run_time for task {self.name}: {e}")

        return self.__class__(self.db_task, app=self.app)


class DatabaseScheduler(Scheduler):
    Entry = DatabaseScheduleEntry

    def __init__(self, *args, **kwargs):
        self._schedule = {}
        self._last_reload = datetime.min.replace(tzinfo=timezone.utc)
        self._reload_interval = timedelta(seconds=5)
        super().__init__(*args, **kwargs)
        self.max_interval = 5

    def setup_schedule(self):
        self.install_default_entries(self.schedule)
        self.update_from_dict(self.app.conf.beat_schedule)

    @property
    def schedule(self):
        now = datetime.now(timezone.utc)
        if now - self._last_reload > self._reload_interval:
            self.sync()
            self._last_reload = now
        return self._schedule

    def sync(self):
        logger.debug("Syncing schedule from database...")
        new_schedule = {}

        try:
            with Session(engine) as session:
                statement = select(Task).where(
                    Task.task_type == TaskType.PERIODIC, Task.enabled == True
                )
                tasks = session.exec(statement).all()

                for task in tasks:
                    try:
                        entry = self.Entry(task, app=self.app)
                        if entry.schedule:  # Only add if schedule is valid
                            new_schedule[task.name] = entry
                    except Exception as e:
                        logger.error(f"Error loading task {task.name}: {e}")
        except Exception as e:
            logger.error(f"Error syncing schedule from database: {e}")

        self._schedule = new_schedule
