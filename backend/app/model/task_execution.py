import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel

if TYPE_CHECKING:
    from .task import Task


class TaskExecutionStatus(str):
    """任务执行状态"""

    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskExecutionBase(SQLModel):
    task_id: uuid.UUID = Field(foreign_key="tasks.id")
    task_name: str | None = Field(default=None, max_length=255)
    celery_task_id: str = Field(max_length=255, nullable=False, index=True)
    status: str = Field(max_length=20, default=TaskExecutionStatus.PENDING)

    # 执行信息
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # 执行结果
    result: str | None = Field(default=None)  # JSON格式的执行结果
    traceback: str | None = Field(default=None)  # 错误堆栈信息

    # 执行参数
    args: str | None = Field(default=None)  # JSON格式的参数
    kwargs: str | None = Field(default=None)  # JSON格式的关键字参数

    # 其他信息
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
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    traceback: str | None = None
    args: str | None = None
    kwargs: str | None = None
    worker: str | None = None
    runtime: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TaskExecutionsPublic(SQLModel):
    executions: list[TaskExecutionPublic]
    total: int
