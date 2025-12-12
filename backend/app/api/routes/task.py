import json
import uuid
from datetime import datetime, timezone
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload
from sqlmodel import desc, func, select

from app.api.deps import CeleryDep, CurrentUser, SessionDep
from app.model.base import Message
from app.model.task import (
    PeriodicScheduleType,
    Task,
    TaskCreate,
    TaskPublic,
    TasksPublic,
    TaskStatus,
    TaskType,
    TaskUpdate,
)
from app.model.task_execution import (
    TaskExecution,
    TaskExecutionPublic,
    TaskExecutionsPublic,
)

router = APIRouter(tags=["Task"], prefix="/tasks")


@router.get("/", response_model=TasksPublic)
def read_tasks(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> TasksPublic:
    """
    Retrieve tasks.
    """
    # Build queries for count and data
    count_statement = select(func.count()).select_from(Task)
    data_statement = (
        select(Task).options(joinedload(Task.owner)).offset(skip).limit(limit)
    )

    # Non-superusers can only see their own tasks
    if not current_user.is_superuser:
        count_statement = count_statement.where(Task.owner_id == current_user.id)
        data_statement = data_statement.where(Task.owner_id == current_user.id)

    # Execute queries and return results
    total = session.exec(count_statement).one()
    tasks = session.exec(data_statement).all()

    return TasksPublic(tasks=tasks, total=total)


@router.get("/registered", response_model=list[str])
def get_registered_tasks(
    celery_app: CeleryDep,
    current_user: CurrentUser,
) -> list[str]:
    """
    Get all registered Celery tasks.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    all_tasks = list(celery_app.tasks.keys())
    filtered_tasks = [t for t in all_tasks if not t.startswith("celery.")]

    return filtered_tasks


@router.get("/{task_id}", response_model=TaskPublic)
def read_task(
    session: SessionDep, current_user: CurrentUser, task_id: uuid.UUID
) -> TaskPublic:
    """
    Get task by ID.
    """
    # Fetch task
    task = session.get(Task, task_id)
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
    celery_app: CeleryDep,
    task_in: TaskCreate,
) -> TaskPublic:
    """
    Create new task.
    """
    # Validate task based on type
    if task_in.task_type == TaskType.ASYNC:
        if not task_in.celery_task_name:
            raise HTTPException(
                status_code=400, detail="Celery task name is required for async tasks"
            )
    elif task_in.task_type == TaskType.SCHEDULED:
        if not task_in.celery_task_name:
            raise HTTPException(
                status_code=400,
                detail="Celery task name is required for scheduled tasks",
            )
        if not task_in.scheduled_time:
            raise HTTPException(
                status_code=400, detail="Scheduled time is required for scheduled tasks"
            )
        if task_in.scheduled_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Scheduled time must be in the future"
            )
    elif task_in.task_type == TaskType.PERIODIC:
        if not task_in.celery_task_name:
            raise HTTPException(
                status_code=400,
                detail="Celery task name is required for periodic tasks",
            )
        if not task_in.periodic_schedule_type:
            raise HTTPException(
                status_code=400,
                detail="Periodic schedule type is required for periodic tasks",
            )
        if task_in.periodic_schedule_type == PeriodicScheduleType.CRONTAB:
            if not any(
                [
                    task_in.crontab_minute,
                    task_in.crontab_hour,
                    task_in.crontab_day_of_week,
                    task_in.crontab_day_of_month,
                    task_in.crontab_month_of_year,
                ]
            ):
                raise HTTPException(
                    status_code=400,
                    detail="At least one crontab parameter must be provided for crontab schedule",
                )
        if task_in.periodic_schedule_type == PeriodicScheduleType.INTERVAL:
            if not any(
                [
                    task_in.interval_seconds,
                    task_in.interval_minutes,
                    task_in.interval_hours,
                    task_in.interval_days,
                ]
            ):
                raise HTTPException(
                    status_code=400,
                    detail="At least one interval parameter must be provided for interval schedule",
                )

    # Create task
    task = Task.model_validate(task_in, update={"owner_id": current_user.id})
    session.add(task)
    session.commit()
    session.refresh(task)

    # Prepare task args and kwargs
    args = json.loads(task.celery_task_args) if task.celery_task_args else []
    kwargs = json.loads(task.celery_task_kwargs) if task.celery_task_kwargs else {}

    # Send task to celery worker if async or scheduled
    if task.task_type == TaskType.ASYNC and task.enabled:
        result = celery_app.send_task(
            name=task.celery_task_name,
            args=args,
            kwargs=kwargs,
            headers={"__db_task_id": str(task.id)},
        )
        task.celery_task_id = result.id

    elif task.task_type == TaskType.SCHEDULED and task.enabled:
        result = celery_app.send_task(
            name=task.celery_task_name,
            args=args,
            kwargs=kwargs,
            eta=task.scheduled_time,
            headers={"__db_task_id": str(task.id)},
        )
        task.celery_task_id = result.id

    # Save updates to database
    if task.celery_task_id:
        session.add(task)
        session.commit()

    return task


@router.put("/{task_id}", response_model=TaskPublic)
def update_task(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    celery_app: CeleryDep,
    task_id: uuid.UUID,
    task_in: TaskUpdate,
) -> TaskPublic:
    """
    Update a task.
    """
    # Validate task based on type
    if task_in.task_type == TaskType.ASYNC:
        if not task_in.celery_task_name:
            raise HTTPException(
                status_code=400, detail="Celery task name is required for async tasks"
            )
    elif task_in.task_type == TaskType.SCHEDULED:
        if not task_in.celery_task_name:
            raise HTTPException(
                status_code=400,
                detail="Celery task name is required for scheduled tasks",
            )
        if not task_in.scheduled_time:
            raise HTTPException(
                status_code=400, detail="Scheduled time is required for scheduled tasks"
            )
        if task_in.scheduled_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Scheduled time must be in the future"
            )
    elif task_in.task_type == TaskType.PERIODIC:
        if not task_in.celery_task_name:
            raise HTTPException(
                status_code=400,
                detail="Celery task name is required for periodic tasks",
            )
        if not task_in.periodic_schedule_type:
            raise HTTPException(
                status_code=400,
                detail="Periodic schedule type is required for periodic tasks",
            )
        if task_in.periodic_schedule_type == PeriodicScheduleType.CRONTAB:
            if not any(
                [
                    task_in.crontab_minute,
                    task_in.crontab_hour,
                    task_in.crontab_day_of_week,
                    task_in.crontab_day_of_month,
                    task_in.crontab_month_of_year,
                ]
            ):
                raise HTTPException(
                    status_code=400,
                    detail="At least one crontab parameter must be provided for crontab schedule",
                )
        if task_in.periodic_schedule_type == PeriodicScheduleType.INTERVAL:
            if not any(
                [
                    task_in.interval_seconds,
                    task_in.interval_minutes,
                    task_in.interval_hours,
                    task_in.interval_days,
                ]
            ):
                raise HTTPException(
                    status_code=400,
                    detail="At least one interval parameter must be provided for interval schedule",
                )

    # Fetch task
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Revoke old scheduled task if type unchanged
    if task.task_type != task_in.task_type:
        if task.celery_task_id:
            celery_app.control.revoke(
                task.celery_task_id, terminate=True, signal="SIGKILL", timeout=10
            )
            task.celery_task_id = None

    # Update task fields
    data = task_in.model_dump(exclude_unset=True)
    task.sqlmodel_update(data)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Handle scheduled tasks
    if task.task_type == TaskType.SCHEDULED and task.enabled:
        # Prepare task args and kwargs
        args = json.loads(task.celery_task_args) if task.celery_task_args else []
        kwargs = json.loads(task.celery_task_kwargs) if task.celery_task_kwargs else {}
        # Send task to celery worker
        result = celery_app.send_task(
            name=task.celery_task_name,
            args=args,
            kwargs=kwargs,
            headers={"__db_task_id": str(task.id)},
        )
        # Update task with new celery_task_id
        if result and result.id:
            task.status = TaskStatus.PENDING
            task.celery_task_id = result.id
            session.add(task)
            session.commit()
            session.refresh(task)

    return task


@router.delete("/{task_id}", response_model=Message)
def delete_task(
    session: SessionDep,
    current_user: CurrentUser,
    celery_app: CeleryDep,
    task_id: uuid.UUID,
) -> Message:
    """
    Delete a task.
    """
    # Fetch task
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Revoke related task executions
    statement = select(TaskExecution).where(
        TaskExecution.task_id == task_id, TaskExecution.completed_at is None
    )
    executions = session.exec(statement).all()
    for execution in executions:
        if execution.celery_task_id:
            celery_app.control.revoke(
                execution.celery_task_id, terminate=True, signal="SIGKILL", timeout=10
            )

    # Delete task
    session.delete(task)
    session.commit()

    return Message(message="Task deleted successfully")


@router.post("/{task_id}/execute", response_model=TaskPublic)
def trigger_task(
    session: SessionDep,
    current_user: CurrentUser,
    celery_app: CeleryDep,
    task_id: uuid.UUID,
) -> TaskPublic:
    """
    Manually trigger task execution.
    """
    # Fetch task
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Ensure task is enabled
    if not task.enabled:
        raise HTTPException(status_code=400, detail="Task is disabled")

    # Prepare task args and kwargs
    args = json.loads(task.celery_task_args) if task.celery_task_args else []
    kwargs = json.loads(task.celery_task_kwargs) if task.celery_task_kwargs else {}

    # Send task to celery worker
    result = celery_app.send_task(
        name=task.celery_task_name,
        args=args,
        kwargs=kwargs,
        headers={"__db_task_id": str(task.id)},
    )

    # Update task with new celery task id
    if result and result.id:
        task.status = TaskStatus.PENDING
        task.celery_task_id = result.id
        session.add(task)
        session.commit()
        session.refresh(task)

    return task


@router.post("/{task_id}/enable", response_model=TaskPublic)
def enable_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> TaskPublic:
    """
    Enable task.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    task.enabled = True
    task.status = TaskStatus.PENDING
    session.add(task)
    session.commit()
    session.refresh(task)

    return task


@router.post("/{task_id}/disable", response_model=TaskPublic)
def disable_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: uuid.UUID,
) -> TaskPublic:
    """
    Disable task.
    """
    # Fetch task
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Disable task
    task.enabled = False
    task.status = TaskStatus.DISABLED

    # Save to database
    session.add(task)
    session.commit()
    session.refresh(task)

    return task


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
    statement = (
        select(TaskExecution)
        .options(joinedload(TaskExecution.task))
        .order_by(desc(TaskExecution.created_at))
        .offset(skip)
        .limit(limit)
    )
    executions = session.exec(statement).all()

    # 如果不是超级用户，过滤掉不属于自己的任务的执行记录
    if not current_user.is_superuser:
        from app.model.task import Task

        tasks_statement = select(Task.id).where(Task.owner_id == current_user.id)
        user_tasks = session.exec(tasks_statement).all()
        user_task_ids = {t.id for t in user_tasks}

        executions = [e for e in executions if e.task_id in user_task_ids]
    statement = select(func.count()).select_from(TaskExecution)
    total = session.exec(statement).one()

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
    execution = session.get(TaskExecution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # 检查权限
    task = session.get(Task, execution.task_id)
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
    execution = session.get(TaskExecution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # 检查权限
    task = session.get(Task, execution.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    session.delete(execution)
    session.commit()
    return Message(message="Execution deleted successfully")


@router.get("/{task_id}/status")
def get_task_execution_status(
    session: SessionDep,
    current_user: CurrentUser,
    celery_app: CeleryDep,
    task_id: uuid.UUID,
) -> Any:
    """
    Get task execution status.
    """
    task = session.get(Task, task_id)
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
        celery_task = AsyncResult(task.celery_task_id, app=celery_app)
        return {
            "task_id": str(task.id),
            "celery_task_id": task.celery_task_id,
            "status": celery_task.status,
            "result": celery_task.result if celery_task.ready() else None,
            "traceback": celery_task.traceback if celery_task.failed() else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


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
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_superuser and (task.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    statement = (
        select(TaskExecution)
        .where(TaskExecution.task_id == task_id)
        .order_by(desc(TaskExecution.created_at))
        .offset(skip)
        .limit(limit)
    )
    executions = session.exec(statement).all()
    statement = select(TaskExecution).where(TaskExecution.task_id == task_id)
    total = len(session.exec(statement).all())

    return TaskExecutionsPublic(executions=executions, total=total)
