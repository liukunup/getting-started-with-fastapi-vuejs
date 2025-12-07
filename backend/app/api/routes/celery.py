from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.api.deps import CeleryDep, CurrentUser

router = APIRouter(prefix="/celery", tags=["celery"])


@router.get("/workers")
def get_workers(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有活跃的Celery Worker信息
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        # 获取活跃的workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        stats = inspect.stats()

        workers_info = []
        if stats:
            for worker_name, worker_stats in stats.items():
                worker_info = {
                    "name": worker_name,
                    "status": "online",
                    "stats": worker_stats,
                    "active_tasks": active_workers.get(worker_name, [])
                    if active_workers
                    else [],
                    "registered_tasks": registered_tasks.get(worker_name, [])
                    if registered_tasks
                    else [],
                }
                workers_info.append(worker_info)

        return {"workers": workers_info, "total": len(workers_info)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get workers info: {str(e)}"
        )


@router.get("/tasks/active")
def get_active_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有活跃的任务
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        tasks_list = []
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    tasks_list.append(
                        {
                            "id": task.get("id"),
                            "name": task.get("name"),
                            "args": task.get("args"),
                            "kwargs": task.get("kwargs"),
                            "worker": worker,
                            "time_start": task.get("time_start"),
                        }
                    )

        return {"tasks": tasks_list, "total": len(tasks_list)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get active tasks: {str(e)}"
        )


@router.get("/tasks/scheduled")
def get_scheduled_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有计划任务
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        inspect = celery_app.control.inspect()
        scheduled_tasks = inspect.scheduled()

        tasks_list = []
        if scheduled_tasks:
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    tasks_list.append(
                        {
                            "id": task.get("request", {}).get("id"),
                            "name": task.get("request", {}).get("name"),
                            "args": task.get("request", {}).get("args"),
                            "kwargs": task.get("request", {}).get("kwargs"),
                            "worker": worker,
                            "eta": task.get("eta"),
                        }
                    )

        return {"tasks": tasks_list, "total": len(tasks_list)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduled tasks: {str(e)}"
        )


@router.get("/tasks/reserved")
def get_reserved_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有保留任务
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        inspect = celery_app.control.inspect()
        reserved_tasks = inspect.reserved()

        tasks_list = []
        if reserved_tasks:
            for worker, tasks in reserved_tasks.items():
                for task in tasks:
                    tasks_list.append(
                        {
                            "id": task.get("id"),
                            "name": task.get("name"),
                            "args": task.get("args"),
                            "kwargs": task.get("kwargs"),
                            "worker": worker,
                        }
                    )

        return {"tasks": tasks_list, "total": len(tasks_list)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get reserved tasks: {str(e)}"
        )


@router.get("/tasks/{task_id}")
def get_task_status(
    task_id: str, current_user: CurrentUser, celery_app: CeleryDep
) -> Any:
    """
    获取指定任务的状态
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        task_result = AsyncResult(task_id, app=celery_app)

        result = {
            "task_id": task_id,
            "status": task_result.status,
            "result": None,
            "traceback": None,
        }

        if task_result.ready():
            if task_result.successful():
                result["result"] = task_result.result
            else:
                result["traceback"] = task_result.traceback

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/tasks/{task_id}/revoke")
def revoke_task(task_id: str, current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    撤销指定的任务
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {"message": f"Task {task_id} has been revoked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke task: {str(e)}")


@router.get("/stats")
def get_celery_stats(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取Celery统计信息
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        inspect = celery_app.control.inspect()

        # 获取各种任务数量
        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        reserved = inspect.reserved() or {}

        active_count = sum(len(tasks) for tasks in active.values())
        scheduled_count = sum(len(tasks) for tasks in scheduled.values())
        reserved_count = sum(len(tasks) for tasks in reserved.values())

        # 获取worker数量
        stats = inspect.stats() or {}
        worker_count = len(stats)

        return {
            "workers": {
                "total": worker_count,
                "online": worker_count,
            },
            "tasks": {
                "active": active_count,
                "scheduled": scheduled_count,
                "reserved": reserved_count,
                "total": active_count + scheduled_count + reserved_count,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get celery_app stats: {str(e)}"
        )


@router.get("/registered-tasks")
def get_registered_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有已注册的任务类型
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        inspect = celery_app.control.inspect()
        registered = inspect.registered()

        all_tasks = set()
        if registered:
            for worker_tasks in registered.values():
                all_tasks.update(worker_tasks)

        return {"tasks": sorted(list(all_tasks)), "total": len(all_tasks)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get registered tasks: {str(e)}"
        )
