import uuid

from sqlmodel import Session, select

from app.model.task import Task, TaskCreate, TaskUpdate


def create_task(
    *, session: Session, task_create: TaskCreate, owner_id: uuid.UUID
) -> Task:
    db_obj = Task.model_validate(task_create, update={"owner_id": owner_id})
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_task(*, session: Session, task_id: uuid.UUID) -> Task | None:
    return session.get(Task, task_id)


def get_tasks_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Task]:
    statement = select(Task).where(Task.owner_id == owner_id).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_all_tasks(*, session: Session, skip: int = 0, limit: int = 100) -> list[Task]:
    statement = select(Task).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_enabled_tasks(*, session: Session) -> list[Task]:
    """获取所有启用的任务"""
    statement = select(Task).where(Task.enabled == True)
    return session.exec(statement).all()


def update_task(*, session: Session, db_task: Task, task_update: TaskUpdate) -> Task:
    task_data = task_update.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(task_data)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


def delete_task(*, session: Session, db_task: Task) -> None:
    session.delete(db_task)
    session.commit()
