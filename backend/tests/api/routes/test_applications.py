from fastapi.testclient import TestClient
from app.core.config import settings
from tests.utils import random_lower_string

def test_create_application(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test App", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/apps/",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "app_id" in content
    assert "app_key" in content

def test_read_applications(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test App", "description": "Test Description"}
    client.post(
        f"{settings.API_V1_STR}/apps/",
        headers=superuser_token_headers,
        json=data,
    )
    
    r = client.get(
        f"{settings.API_V1_STR}/apps/",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    content = r.json()
    assert len(content["applications"]) >= 1
    assert content["total"] >= 1


def test_read_application(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test App", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/apps/",
        headers=superuser_token_headers,
        json=data,
    )
    app_id = r.json()["id"]

    r = client.get(
        f"{settings.API_V1_STR}/apps/{app_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == data["name"]
    assert content["id"] == app_id

def test_update_application(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test App", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/apps/",
        headers=superuser_token_headers,
        json=data,
    )
    app_id = r.json()["id"]

    update_data = {"name": "Updated App", "description": "Updated Description"}
    r = client.put(
        f"{settings.API_V1_STR}/apps/{app_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == update_data["name"]
    assert content["description"] == update_data["description"]

def test_delete_application(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test App", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/apps/",
        headers=superuser_token_headers,
        json=data,
    )
    app_id = r.json()["id"]
    
    r = client.delete(
        f"{settings.API_V1_STR}/apps/{app_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    
    r = client.get(
        f"{settings.API_V1_STR}/apps/{app_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
