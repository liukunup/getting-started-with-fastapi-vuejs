import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel, DateTime

if TYPE_CHECKING:
    from .task import Task


class TaskExecutionStatus(str, Enum):
    """任务执行状态"""

    PENDING = "pending"  # 等待中
    STARTED = "started"  # 已开始
    RUNNING = "running"  # 运行中
    SUCCESS = "success"  # 执行成功
    FAILED = "failed"  # 执行失败
    RETRYING = "retrying"  # 重试中
    REVOKED = "revoked"  # 已撤销
    DISABLED = "disabled"  # 已禁用


class TaskExecutionBase(SQLModel):
    task_id: uuid.UUID = Field(foreign_key="tasks.id")
    task_name: str | None = Field(default=None, max_length=255)
    celery_task_id: str = Field(max_length=255, nullable=False, unique=True, index=True)
    celery_task_args: str | None = Field(default=None)  # JSON格式的参数
    celery_task_kwargs: str | None = Field(default=None)  # JSON格式的关键字参数
    status: str = Field(max_length=20, default=TaskExecutionStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    result: str | None = Field(default=None)  # JSON格式的执行结果
    traceback: str | None = Field(default=None)  # 错误堆栈信息
    worker: str | None = Field(default=None, max_length=255)  # 执行的worker名称
    runtime: float | None = Field(default=None)  # 执行时长（秒）


class TaskExecutionCreate(TaskExecutionBase):
    pass


class TaskExecutionUpdate(SQLModel):
    status: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    traceback: str | None = None
    worker: str | None = None
    runtime: float | None = None


class TaskExecution(TaskExecutionBase, BaseDataModel, table=True):
    __tablename__ = "task_executions"

    task: Optional["Task"] = Relationship(back_populates="executions")


class TaskExecutionPublic(SQLModel):
    id: uuid.UUID
    task_id: uuid.UUID
    task_name: str | None = None
    celery_task_id: str
    celery_task_args: str | None = None
    celery_task_kwargs: str | None = None
    status: str
    started_at: DateTime | None = None
    completed_at: DateTime | None = None
    result: str | None = None
    traceback: str | None = None
    worker: str | None = None
    runtime: float | None = None
    created_at: DateTime | None = None
    updated_at: DateTime | None = None


class TaskExecutionsPublic(SQLModel):
    executions: list[TaskExecutionPublic]
    total: int
