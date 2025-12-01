from fastapi.testclient import TestClient
from app.core.config import settings
from tests.utils import random_lower_string

def test_create_group(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test Group", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/groups/",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "id" in content

def test_read_groups(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test Group", "description": "Test Description"}
    client.post(
        f"{settings.API_V1_STR}/groups/",
        headers=superuser_token_headers,
        json=data,
    )
    
    r = client.get(
        f"{settings.API_V1_STR}/groups/",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    content = r.json()
    assert len(content["groups"]) >= 1
    assert content["total"] >= 1

def test_read_group(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test Group", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/groups/",
        headers=superuser_token_headers,
        json=data,
    )
    group_id = r.json()["id"]
    
    r = client.get(
        f"{settings.API_V1_STR}/groups/{group_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == data["name"]
    assert content["id"] == group_id

def test_update_group(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test Group", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/groups/",
        headers=superuser_token_headers,
        json=data,
    )
    group_id = r.json()["id"]
    
    update_data = {"name": "Updated Group", "description": "Updated Description"}
    r = client.put(
        f"{settings.API_V1_STR}/groups/{group_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["name"] == update_data["name"]
    assert content["description"] == update_data["description"]

def test_delete_group(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Test Group", "description": "Test Description"}
    r = client.post(
        f"{settings.API_V1_STR}/groups/",
        headers=superuser_token_headers,
        json=data,
    )
    group_id = r.json()["id"]
    
    r = client.delete(
        f"{settings.API_V1_STR}/groups/{group_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Group deleted successfully"
    
    r = client.get(
        f"{settings.API_V1_STR}/groups/{group_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
