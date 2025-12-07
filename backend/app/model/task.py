import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel, DateTime
from .user import UserPublic

if TYPE_CHECKING:
    from .task_execution import TaskExecution
    from .user import User


class TaskType(str, Enum):
    """任务类型"""

    ASYNC = "async"  # 异步任务
    SCHEDULED = "scheduled"  # 定时任务
    PERIODIC = "periodic"  # 周期任务


class PeriodicScheduleType(str, Enum):
    """周期任务调度类型"""

    CRONTAB = "crontab"  # 使用crontab表达式
    INTERVAL = "interval"  # 使用固定间隔


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"  # 等待中
    STARTED = "started"  # 已开始
    RUNNING = "running"  # 运行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    REVOKED = "revoked"  # 已撤销
    DISABLED = "disabled"  # 已禁用


class TaskBase(SQLModel):
    name: str = Field(max_length=255, nullable=False, index=True)
    description: str | None = Field(default=None, max_length=512)
    task_type: TaskType = Field(
        default=TaskType.ASYNC, sa_column=Column(String(20), nullable=False)
    )

    # Celery任务相关
    celery_task_name: str = Field(
        max_length=255, nullable=False
    )  # Celery任务名称，如 app.api.tasks.demo_async_task
    celery_task_args: str | None = Field(default=None)  # JSON格式的任务参数
    celery_task_kwargs: str | None = Field(default=None)  # JSON格式的任务关键字参数

    # 定时配置
    scheduled_time: datetime | None = Field(default=None)  # 定时执行时间

    # 周期任务调度配置
    periodic_schedule_type: PeriodicScheduleType | None = Field(
        default=None, sa_column=Column(String(20), nullable=True)
    )  # 周期调度类型

    # Crontab配置
    crontab_minute: str | None = Field(default="*", max_length=64)  # 分钟 (0-59)
    crontab_hour: str | None = Field(default="*", max_length=64)  # 小时 (0-23)
    crontab_day_of_week: str | None = Field(
        default="*", max_length=64
    )  # 星期 (0-6, 0为周日)
    crontab_day_of_month: str | None = Field(default="*", max_length=64)  # 日期 (1-31)
    crontab_month_of_year: str | None = Field(default="*", max_length=64)  # 月份 (1-12)

    # Interval配置
    interval_seconds: int | None = Field(default=None)  # 间隔秒数
    interval_minutes: int | None = Field(default=None)  # 间隔分钟数
    interval_hours: int | None = Field(default=None)  # 间隔小时数
    interval_days: int | None = Field(default=None)  # 间隔天数

    # 任务状态
    status: TaskStatus = Field(default=TaskStatus.PENDING, sa_column=Column(String(20)))
    enabled: bool = Field(default=True)  # 是否启用

    # 执行记录
    last_run_time: datetime | None = Field(default=None)  # 最后执行时间
    next_run_time: datetime | None = Field(default=None)  # 下次执行时间
    celery_task_id: str | None = Field(
        default=None, max_length=255
    )  # 最近的Celery任务ID


class TaskCreate(TaskBase):
    owner_id: uuid.UUID | None = None


class TaskUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    task_type: TaskType | None = None
    celery_task_name: str | None = None
    celery_task_args: str | None = None
    celery_task_kwargs: str | None = None
    scheduled_time: datetime | None = None
    periodic_schedule_type: PeriodicScheduleType | None = None
    crontab_minute: str | None = None
    crontab_hour: str | None = None
    crontab_day_of_week: str | None = None
    crontab_day_of_month: str | None = None
    crontab_month_of_year: str | None = None
    interval_seconds: int | None = None
    interval_minutes: int | None = None
    interval_hours: int | None = None
    interval_days: int | None = None
    status: TaskStatus | None = None
    enabled: bool | None = None
    last_run_time: datetime | None = None
    next_run_time: datetime | None = None
    celery_task_id: str | None = None
    owner_id: uuid.UUID | None = None


class Task(TaskBase, BaseDataModel, table=True):
    __tablename__ = "tasks"

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    owner: Optional["User"] = Relationship(back_populates="tasks")

    executions: list["TaskExecution"] = Relationship(
        back_populates="task", cascade_delete=True
    )


class TaskPublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    task_type: TaskType
    celery_task_name: str
    celery_task_args: str | None = None
    celery_task_kwargs: str | None = None
    scheduled_time: DateTime | None = None
    periodic_schedule_type: PeriodicScheduleType | None = None
    crontab_minute: str | None = None
    crontab_hour: str | None = None
    crontab_day_of_week: str | None = None
    crontab_day_of_month: str | None = None
    crontab_month_of_year: str | None = None
    interval_seconds: int | None = None
    interval_minutes: int | None = None
    interval_hours: int | None = None
    interval_days: int | None = None
    status: TaskStatus
    enabled: bool
    last_run_time: DateTime | None = None
    next_run_time: DateTime | None = None
    celery_task_id: str | None = None
    owner: UserPublic | None = None
    created_at: DateTime | None = None
    updated_at: DateTime | None = None


class TasksPublic(SQLModel):
    tasks: list[TaskPublic]
    total: int
