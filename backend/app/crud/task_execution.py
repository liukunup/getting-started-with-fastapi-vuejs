import uuid
from sqlalchemy.orm import joinedload

from sqlmodel import Session, desc, select

from app.model.task_execution import (
    TaskExecution,
    TaskExecutionCreate,
    TaskExecutionUpdate,
)


def create_execution(
    *, session: Session, execution_create: TaskExecutionCreate
) -> TaskExecution:
    db_obj = TaskExecution.model_validate(execution_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_execution(*, session: Session, execution_id: uuid.UUID) -> TaskExecution | None:
    return session.get(TaskExecution, execution_id)


def get_execution_by_celery_task_id(
    *, session: Session, celery_task_id: str
) -> TaskExecution | None:
    statement = select(TaskExecution).where(
        TaskExecution.celery_task_id == celery_task_id
    )
    return session.exec(statement).first()


def get_executions_by_task(
    *, session: Session, task_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[TaskExecution]:
    statement = (
        select(TaskExecution)
        .where(TaskExecution.task_id == task_id)
        .order_by(desc(TaskExecution.created_at))
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def get_latest_execution(
    *, session: Session, task_id: uuid.UUID
) -> TaskExecution | None:
    statement = (
        select(TaskExecution)
        .where(TaskExecution.task_id == task_id)
        .order_by(desc(TaskExecution.created_at))
        .limit(1)
    )
    return session.exec(statement).first()


def update_execution(
    *,
    session: Session,
    db_execution: TaskExecution,
    execution_update: TaskExecutionUpdate,
) -> TaskExecution:
    execution_data = execution_update.model_dump(exclude_unset=True)
    db_execution.sqlmodel_update(execution_data)
    session.add(db_execution)
    session.commit()
    session.refresh(db_execution)
    return db_execution


def delete_execution(*, session: Session, db_execution: TaskExecution) -> None:
    session.delete(db_execution)
    session.commit()


def count_executions_by_task(*, session: Session, task_id: uuid.UUID) -> int:
    statement = select(TaskExecution).where(TaskExecution.task_id == task_id)
    return len(session.exec(statement).all())


def get_all_executions(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[TaskExecution]:
    """获取所有任务执行记录"""
    statement = (
        select(TaskExecution)
        .options(joinedload(TaskExecution.task))
        .order_by(desc(TaskExecution.created_at))
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def count_all_executions(*, session: Session) -> int:
    """统计所有执行记录数量"""
    from sqlmodel import func

    statement = select(func.count()).select_from(TaskExecution)
    return session.exec(statement).one()
