from fastapi.testclient import TestClient
from app.core.config import settings
from unittest.mock import patch

def test_health_check(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/healthz/")
    assert r.status_code == 200
    assert r.json() is True

def test_test_email(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.utils.send_email") as mock_send_email:
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            headers=superuser_token_headers,
            params={"email_to": "test@example.com"},
        )
        assert r.status_code == 201
        assert "message" in r.json()
        assert mock_send_email.called

def test_celery_endpoint(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.utils.test_celery.delay") as mock_celery:
        mock_celery.return_value.id = "test_id"
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-celery/",
            headers=superuser_token_headers,
            params={"msg": "test"},
        )
        assert r.status_code == 201
        assert "message" in r.json()
        assert mock_celery.called

def test_long_task(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.utils.long_running_task.delay") as mock_celery:
        mock_celery.return_value.id = "test_id"
        r = client.post(
            f"{settings.API_V1_STR}/utils/long-task/",
            headers=superuser_token_headers,
            params={"seconds": 1},
        )
        assert r.status_code == 201
        assert "message" in r.json()
        assert mock_celery.called

def test_get_task_status(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.utils.AsyncResult") as mock_async_result:
        mock_async_result.return_value.status = "SUCCESS"
        mock_async_result.return_value.result = "Done"
        
        r = client.get(
            f"{settings.API_V1_STR}/utils/task-status/test_id",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        result = r.json()
        assert result["status"] == "SUCCESS"
        assert result["result"] == "Done"
