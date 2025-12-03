import json
import uuid
from datetime import datetime
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, TaskQueueDep
from app.core.config import settings
from app.core.storage import storage
from app.crud import task as task_crud
from app.crud import task_execution as execution_crud
from app.model.base import Message
from app.model.task import (
    Task,
    TaskCreate,
    TaskPublic,
    TasksPublic,
    TaskStatus,
    TaskType,
    TaskUpdate,
    PeriodicScheduleType,
)
from app.model.task_execution import (
    TaskExecutionCreate,
    TaskExecutionPublic,
    TaskExecutionsPublic,
)
from app.model.user import User

router = APIRouter(tags=["Task"], prefix="/tasks")


def convert_user_avatar_to_url(user: User) -> None:
    """Convert avatar path to full MinIO public URL for a user object."""
    if user and user.avatar and not user.avatar.startswith('http'):
        user.avatar = storage.get_file_url(user.avatar)


@router.get("/registered", response_model=list[str])
def get_registered_tasks(
    task_queue: TaskQueueDep,
    current_user: CurrentUser,
) -> list[str]:
    """
    Get all registered Celery tasks.
    """
    return task_queue.get_registered_tasks()


@router.get("/executions/all", response_model=TaskExecutionsPublic)
def get_all_task_executions(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> TaskExecutionsPublic:
    """
    获取所有任务执行记录（仅管理员或自己的任务）
    """
    executions = execution_crud.get_all_executions(
        session=session, skip=skip, limit=limit
    )

    # 如果不是超级用户，过滤掉不属于自己的任务的执行记录
    if not current_user.is_superuser:
        from app.model.task import Task

        user_task_ids = set()
        tasks_statement = select(Task.id).where(Task.owner_id == current_user.id)
        user_tasks = session.exec(tasks_statement).all()
        user_task_ids = {task for task in user_tasks}

        executions = [e for e in executions if e.task_id in user_task_ids]

    total = execution_crud.count_all_executions(session=session)

    execution_public_list = []
    for e in executions:
        e_public = TaskExecutionPublic.model_validate(e)
        if not e_public.task_name and e.task:
            e_public.task_name = e.task.name
        execution_public_list.append(e_public)

    return TaskExecutionsPublic(executions=execution_public_list, total=total)


@router.get("/executions/{execution_id}", response_model=TaskExecutionPublic)
def get_execution(
    session: SessionDep,
    current_user: CurrentUser,
    execution_id: uuid.UUID,
) -> TaskExecutionPublic:
    """
    获取执行记录详情
    """
    execution = execution_crud.get_execution(session=session, execution_id=execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # 检查权限
    task = task_crud.get_task(session=session, task_id=execution.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    execution_public = TaskExecutionPublic.model_validate(execution)
    if not execution_public.task_name:
        execution_public.task_name = task.name
    return execution_public


@router.delete("/executions/{execution_id}", response_model=Message)
def delete_execution(
    session: SessionDep,
    current_user: CurrentUser,
    execution_id: uuid.UUID,
) -> Message:
    """
    删除执行记录
    """
    execution = execution_crud.get_execution(session=session, execution_id=execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # 检查权限
    task = task_crud.get_task(session=session, task_id=execution.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    execution_crud.delete_execution(session=session, db_execution=execution)
    session.commit()

    return Message(message="Execution deleted successfully")


@router.get("/", response_model=TasksPublic)
def read_tasks(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> TasksPublic:
    """
    Retrieve tasks.
    """
    # Get total count
    count_statement = select(func.count()).select_from(Task)
    # Get tasks with pagination
    data_statement = (
        select(Task).options(joinedload(Task.owner)).offset(skip).limit(limit)
    )

    # Non-superusers can only see their own tasks
    if not current_user.is_superuser:
        count_statement = count_statement.where(Task.owner_id == current_user.id)
        data_statement = data_statement.where(Task.owner_id == current_user.id)

    # Execute queries
    total = session.exec(count_statement).one()
    tasks = session.exec(data_statement).all()
    # Convert owner avatar paths to URLs
    for task in tasks:
        if task.owner:
            convert_user_avatar_to_url(task.owner)

    return TasksPublic(tasks=tasks, total=total)


@router.get("/{task_id}", response_model=TaskPublic)
def read_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> TaskPublic:
    """
    Get task by ID.
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return task


@router.post("/", response_model=TaskPublic)
def create_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_queue: TaskQueueDep,
    task_in: TaskCreate,
) -> TaskPublic:
    """
    Create new task.
    """
    # Validate task configuration
    if task_in.task_type == TaskType.SCHEDULED and not task_in.scheduled_time:
        raise HTTPException(
            status_code=400, detail="Scheduled time is required for scheduled tasks"
        )

    if task_in.task_type == TaskType.PERIODIC:
        # 验证周期任务配置
        if not task_in.periodic_schedule_type:
            raise HTTPException(
                status_code=400, detail="Periodic schedule type is required for periodic tasks"
            )
        
        if task_in.periodic_schedule_type == PeriodicScheduleType.INTERVAL:
            # 验证interval配置
            if not any([
                task_in.interval_seconds,
                task_in.interval_minutes,
                task_in.interval_hours,
                task_in.interval_days
            ]):
                raise HTTPException(
                    status_code=400,
                    detail="At least one interval parameter must be provided for interval schedule"
                )

    task = task_crud.create_task(
        session=session, task_create=task_in, owner_id=current_user.id
    )

    execute_task(session=session, task_queue=task_queue, db_task=task)

    return task


@router.put("/{task_id}", response_model=TaskPublic)
def update_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    task_in: TaskUpdate,
) -> TaskPublic:
    """
    Update a task.
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    task = task_crud.update_task(session=session, db_task=task, task_update=task_in)
    return task


@router.delete("/{task_id}", response_model=Message)
def delete_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_queue: TaskQueueDep,
    task_id: uuid.UUID,
) -> Message:
    """
    Delete a task.
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    if task.task_type == TaskType.PERIODIC:
        task_queue.unregister_periodic_task(task.name)

    task_crud.delete_task(session=session, db_task=task)
    return Message(message="Task deleted successfully")


@router.post("/{task_id}/execute", response_model=TaskPublic)
def trigger_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_queue: TaskQueueDep,
    task_id: uuid.UUID,
) -> TaskPublic:
    """
    Manually trigger task execution.
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    if not task.enabled:
        raise HTTPException(status_code=400, detail="Task is disabled")

    execute_task(session=session, task_queue=task_queue, db_task=task)

    return task


@router.post("/{task_id}/enable", response_model=TaskPublic)
def enable_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_queue: TaskQueueDep,
    task_id: uuid.UUID,
) -> TaskPublic:
    """
    Enable task.
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    task.enabled = True
    task.status = TaskStatus.PENDING
    session.add(task)
    session.commit()
    session.refresh(task)

    # 如果是周期性任务，注册到Celery Beat
    if task.task_type == TaskType.PERIODIC:
        schedule_config = {
            "schedule_type": task.periodic_schedule_type,
        }
        if task.periodic_schedule_type == PeriodicScheduleType.CRONTAB:
            schedule_config.update({
                "minute": task.crontab_minute or "*",
                "hour": task.crontab_hour or "*",
                "day_of_week": task.crontab_day_of_week or "*",
                "day_of_month": task.crontab_day_of_month or "*",
                "month_of_year": task.crontab_month_of_year or "*",
            })
        elif task.periodic_schedule_type == PeriodicScheduleType.INTERVAL:
            schedule_config.update({
                "seconds": task.interval_seconds or 0,
                "minutes": task.interval_minutes or 0,
                "hours": task.interval_hours or 0,
                "days": task.interval_days or 0,
            })
        
        task_queue.register_periodic_task(
            task_name=task.name,
            celery_task_name=task.celery_task_name,
            schedule_config=schedule_config
        )

    return task


@router.post("/{task_id}/disable", response_model=TaskPublic)
def disable_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_queue: TaskQueueDep,
    task_id: uuid.UUID,
) -> TaskPublic:
    """
    Disable task.
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    task.enabled = False
    task.status = TaskStatus.DISABLED
    session.add(task)
    session.commit()
    session.refresh(task)

    # 如果是周期性任务，从Celery Beat移除
    if task.task_type == TaskType.PERIODIC:
        task_queue.unregister_periodic_task(task.name)

    return task


@router.get("/{task_id}/status")
def get_task_execution_status(
    session: SessionDep,
    current_user: CurrentUser,
    task_queue: TaskQueueDep,
    task_id: uuid.UUID,
) -> Any:
    """
    Get task execution status.
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    if not task.celery_task_id:
        return {
            "task_id": str(task.id),
            "celery_task_id": None,
            "status": task.status,
            "message": "No execution record",
        }

    try:
        celery_task = AsyncResult(task.celery_task_id, app=task_queue.celery)
        return {
            "task_id": str(task.id),
            "celery_task_id": task.celery_task_id,
            "status": celery_task.status,
            "result": celery_task.result if celery_task.ready() else None,
            "traceback": celery_task.traceback if celery_task.failed() else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get task status: {str(e)}"
        )


def execute_task(*, session: SessionDep, task_queue: TaskQueueDep, db_task: Task) -> None:
    """
    Execute a task by sending it to the Celery worker.
    """
    try:
        # 使用TaskManager执行任务
        celery_task_id = task_queue.execute_task(db_task)

        # 创建执行记录
        execution_create = TaskExecutionCreate(
            task_id=db_task.id,
            celery_task_id=celery_task_id,
            status="pending",
            args=db_task.task_args,
            kwargs=db_task.task_kwargs,
            started_at=datetime.utcnow(),
        )
        execution_crud.create_execution(
            session=session, execution_create=execution_create
        )

        # 更新任务状态
        db_task.celery_task_id = celery_task_id
        db_task.status = TaskStatus.RUNNING
        db_task.last_run_time = datetime.utcnow()
        session.add(db_task)
        session.commit()

    except Exception as e:
        db_task.status = TaskStatus.FAILED
        session.add(db_task)
        session.commit()
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")


@router.get("/{task_id}/executions", response_model=TaskExecutionsPublic)
def get_task_executions(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> TaskExecutionsPublic:
    """
    获取任务的执行记录
    """
    task = task_crud.get_task(session=session, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    executions = execution_crud.get_executions_by_task(
        session=session, task_id=task_id, skip=skip, limit=limit
    )
    total = execution_crud.count_executions_by_task(session=session, task_id=task_id)

    return TaskExecutionsPublic(executions=executions, total=total)
