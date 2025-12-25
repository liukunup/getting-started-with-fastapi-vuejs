import asyncio
import json
import time
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.api.deps import CeleryDep, CurrentUser
from app.core.cache import cache

router = APIRouter(tags=["Celery"], prefix="/celery")


def get_inspect_data(celery_app, method_name: str) -> dict | None:
    """
    Get Celery inspect data with caching and locking to prevent dogpile effect
    """
    cache_key = f"celery:inspect:{method_name}"
    lock_key = f"celery:inspect:lock:{method_name}"

    # 1. Try to get from cache
    try:
        cached_data = cache.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception:
        pass

    # 2. Try to acquire lock
    acquired_lock = False
    try:
        # Try to acquire lock for 5 seconds
        acquired_lock = cache.redis.set(lock_key, "1", ex=5, nx=True)
    except Exception:
        pass

    if acquired_lock:
        try:
            # We have the lock, perform the inspection
            inspect = celery_app.control.inspect(timeout=1.0)
            method = getattr(inspect, method_name)
            data = method()

            # Cache the result
            if data is not None:
                try:
                    cache.redis.set(cache_key, json.dumps(data), ex=15)
                except Exception:
                    pass
            return data
        except Exception:
            return None
        finally:
            # Release lock
            try:
                cache.redis.delete(lock_key)
            except Exception:
                pass
    else:
        # Lock is held by someone else, wait for result
        for _ in range(20):  # Wait up to 2 seconds (20 * 0.1s)
            time.sleep(0.1)
            try:
                cached_data = cache.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception:
                pass

        # If we timed out waiting, return None (or could try to fetch ourselves)
        return None


@router.get("/workers", summary="Get active Celery workers")
async def get_workers(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有活跃的Celery Worker信息
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        # Run inspections in parallel
        loop = asyncio.get_running_loop()

        active_future = loop.run_in_executor(
            None, get_inspect_data, celery_app, "active"
        )
        registered_future = loop.run_in_executor(
            None, get_inspect_data, celery_app, "registered"
        )
        stats_future = loop.run_in_executor(None, get_inspect_data, celery_app, "stats")

        active_workers = await active_future
        registered_tasks = await registered_future
        stats = await stats_future

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


@router.get("/tasks/active", summary="Get active Celery tasks")
def get_active_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有活跃的任务
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        active_tasks = get_inspect_data(celery_app, "active")

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


@router.get("/tasks/scheduled", summary="Get scheduled Celery tasks")
def get_scheduled_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有计划任务
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        scheduled_tasks = get_inspect_data(celery_app, "scheduled")

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


@router.get("/tasks/reserved", summary="Get reserved Celery tasks")
def get_reserved_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有保留任务
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        reserved_tasks = get_inspect_data(celery_app, "reserved")

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


@router.get("/tasks/{task_id}", summary="Get Celery task status")
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


@router.post("/tasks/{task_id}/revoke", summary="Revoke a Celery task")
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


@router.get("/stats", summary="Get Celery statistics")
async def get_celery_stats(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取Celery统计信息
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        # Run inspections in parallel
        loop = asyncio.get_running_loop()

        active_future = loop.run_in_executor(
            None, get_inspect_data, celery_app, "active"
        )
        scheduled_future = loop.run_in_executor(
            None, get_inspect_data, celery_app, "scheduled"
        )
        reserved_future = loop.run_in_executor(
            None, get_inspect_data, celery_app, "reserved"
        )
        stats_future = loop.run_in_executor(None, get_inspect_data, celery_app, "stats")

        active = await active_future or {}
        scheduled = await scheduled_future or {}
        reserved = await reserved_future or {}
        stats = await stats_future or {}

        active_count = sum(len(tasks) for tasks in active.values())
        scheduled_count = sum(len(tasks) for tasks in scheduled.values())
        reserved_count = sum(len(tasks) for tasks in reserved.values())

        # 获取worker数量
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


@router.get("/registered-tasks", summary="Get registered Celery tasks")
def get_registered_tasks(current_user: CurrentUser, celery_app: CeleryDep) -> Any:
    """
    获取所有已注册的任务类型
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        registered = get_inspect_data(celery_app, "registered")

        all_tasks = set()
        if registered:
            for worker_tasks in registered.values():
                all_tasks.update(worker_tasks)

        return {"tasks": sorted(all_tasks), "total": len(all_tasks)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get registered tasks: {str(e)}"
        )
