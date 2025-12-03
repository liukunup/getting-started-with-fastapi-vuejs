import json
import logging
from typing import Any

from celery import Celery
from celery.result import AsyncResult
from celery.schedules import crontab, schedule

from app.core.config import settings
from app.model.task import Task, TaskType, PeriodicScheduleType

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self) -> None:
        # 使用已初始化的worker celery实例
        from app.worker import celery_app
        self.__celery = celery_app

    @property
    def celery(self) -> Celery:
        return self.__celery

    def get_registered_tasks(self) -> list[str]:
        """获取所有已注册的Celery任务"""
        # 过滤掉celery内置任务
        return [
            task_name
            for task_name in self.__celery.tasks.keys()
            if not task_name.startswith("celery.")
        ]

    def execute_task(self, task: Task) -> str:
        """执行任务并返回Celery任务ID"""
        # 检查任务是否注册
        if task.celery_task_name not in self.__celery.tasks:
            raise ValueError(f"Task {task.celery_task_name} is not registered in Celery.")
        
        # 解析参数
        args = json.loads(task.task_args) if task.task_args else []
        kwargs = json.loads(task.task_kwargs) if task.task_kwargs else {}

        celery_task = None
        if task.task_type == TaskType.ASYNC:
            celery_task = self.__celery.send_task(task.celery_task_name, args=args, kwargs=kwargs)
        elif task.task_type == TaskType.SCHEDULED:
            # 延迟执行任务
            if not task.scheduled_time:
                raise ValueError("Scheduled time is required for scheduled tasks")
            celery_task = self.__celery.send_task(
                task.celery_task_name,
                args=args,
                kwargs=kwargs,
                eta=task.scheduled_time,
            )
        elif task.task_type == TaskType.PERIODIC:
            # 周期性任务立即执行一次
            celery_task = self.__celery.send_task(task.celery_task_name, args=args, kwargs=kwargs)
        else:
            raise ValueError(f"Unsupported task type: {task.task_type}")

        return celery_task.id

    def get_task_status(self, celery_task_id: str) -> dict[str, Any]:
        """
        获取Celery任务的状态和结果
        """
        result = AsyncResult(celery_task_id, app=self.__celery)
        return {
            "task_id": celery_task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback if result.failed() else None,
        }

    def revoke_task(self, celery_task_id: str, terminate: bool = False) -> None:
        """
        撤销任务
        :param celery_task_id: Celery任务ID
        :param terminate: 是否强制终止正在运行的任务
        """
        self.__celery.control.revoke(celery_task_id, terminate=terminate)

    def register_periodic_task(
        self, task_name: str, celery_task_name: str, schedule_config: dict
    ) -> None:
        """
        动态注册周期性任务到Celery Beat
        :param task_name: 任务标识名称
        :param celery_task_name: Celery任务名称
        :param schedule_config: 调度配置,包含schedule_type和相应的配置参数
        """
        schedule_type = schedule_config.get("schedule_type", "crontab")
        
        if schedule_type == "crontab":
            # 使用crontab调度
            task_schedule = crontab(
                minute=schedule_config.get("minute", "*"),
                hour=schedule_config.get("hour", "*"),
                day_of_week=schedule_config.get("day_of_week", "*"),
                day_of_month=schedule_config.get("day_of_month", "*"),
                month_of_year=schedule_config.get("month_of_year", "*"),
            )
        elif schedule_type == "interval":
            # 使用interval调度
            from datetime import timedelta
            
            seconds = schedule_config.get("seconds", 0)
            minutes = schedule_config.get("minutes", 0)
            hours = schedule_config.get("hours", 0)
            days = schedule_config.get("days", 0)
            
            if not any([seconds, minutes, hours, days]):
                raise ValueError("At least one interval parameter must be provided")
            
            task_schedule = schedule(
                run_every=timedelta(
                    days=days,
                    hours=hours,
                    minutes=minutes,
                    seconds=seconds
                )
            )
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
        
        self.__celery.conf.beat_schedule[task_name] = {
            "task": celery_task_name,
            "schedule": task_schedule,
        }
        logger.info(f"Registered periodic task: {task_name} with {schedule_type} schedule")

    def unregister_periodic_task(self, task_name: str) -> None:
        """移除周期性任务"""
        if task_name in self.__celery.conf.beat_schedule:
            del self.__celery.conf.beat_schedule[task_name]
            logger.info(f"Unregistered periodic task: {task_name}")


distributed_task_queue = TaskManager()
