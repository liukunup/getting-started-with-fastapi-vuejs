from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.model.base import Message, Task
from app.utils import generate_test_email, send_email
from app.worker import long_running_task, test_celery

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(
    email_to: EmailStr,
) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/healthz/")
async def health_check() -> bool:
    return True


@router.post("/test-celery/", response_model=Task, status_code=201)
def test_celery_endpoint(msg: str) -> Any:
    """
    Test Celery worker.
    """
    task = test_celery.delay(msg)
    return Task(task_id=task.id, message="Word received")


@router.post("/long-task/", response_model=Task, status_code=201)
def trigger_long_task(seconds: int) -> Any:
    task = long_running_task.delay(seconds)
    return Task(task_id=task.id, message="Task started")


@router.get("/task-status/{task_id}")
def get_task_status(task_id: str) -> Any:
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result,
    }
