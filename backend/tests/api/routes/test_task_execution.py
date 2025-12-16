from unittest.mock import MagicMock
from sqlmodel import Session, select
from app.core.database import engine
from app.model.task import Task
from app.model.task_execution import TaskExecution
from app.worker.handlers import task_prerun_handler
from fastapi.testclient import TestClient
from app.core.config import settings

def test_task_prerun_handler_saves_task_name(client: TestClient):
    # Create a task in DB
    task_name = "Test Task For Name Persistence"
    celery_task_name = "app.api.tasks.test_celery"
    
    with Session(engine) as session:
        task = Task(name=task_name, celery_task_name=celery_task_name, enabled=True)
        session.add(task)
        session.commit()
        session.refresh(task)
        task_db_id = task.id
        
    task_id = "test_task_id_456"
    mock_task = MagicMock()
    mock_task.name = celery_task_name
    mock_task.request.headers = {"__task_db_id": str(task_db_id)}
    mock_task.request.hostname = "worker@test"
    
    # Call handler
    try:
        task_prerun_handler(task_id=task_id, task=mock_task)
        
        # Verify DB
        with Session(engine) as session:
            statement = select(TaskExecution).where(TaskExecution.celery_task_id == task_id)
            execution = session.exec(statement).first()
            assert execution is not None
            assert execution.task_name == task_name
            assert execution.worker == "worker@test"
            
            # Clean up
            session.delete(execution)
            session.delete(session.get(Task, task_db_id))
            session.commit()
    except Exception as e:
        # Clean up in case of error
        with Session(engine) as session:
            task = session.get(Task, task_db_id)
            if task:
                session.delete(task)
                session.commit()
        raise e
