from fastapi.testclient import TestClient
from app.core.config import settings
from tests.utils import random_lower_string

def test_create_api(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "group": "test_group",
        "name": "test_api",
        "path": "/test/api",
        "method": "GET"
    }
    response = client.post(
        f"{settings.API_V1_STR}/apis/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["group"] == data["group"]
    assert content["name"] == data["name"]
    assert content["path"] == data["path"]
    assert content["method"] == data["method"]
    assert "id" in content

def test_read_api(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "group": "test_group",
        "name": "test_api",
        "path": "/test/api",
        "method": "GET"
    }
    response = client.post(
        f"{settings.API_V1_STR}/apis/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    api_id = response.json()["id"]

    response = client.get(
        f"{settings.API_V1_STR}/apis/{api_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["group"] == data["group"]
    assert content["name"] == data["name"]
    assert content["path"] == data["path"]
    assert content["method"] == data["method"]
    assert content["id"] == api_id

def test_read_apis(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "group": "test_group",
        "name": "test_api",
        "path": "/test/api",
        "method": "GET"
    }
    client.post(
        f"{settings.API_V1_STR}/apis/",
        headers=superuser_token_headers,
        json=data,
    )
    
    response = client.get(
        f"{settings.API_V1_STR}/apis/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 1
    assert content["total"] >= 1

def test_update_api(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "group": "test_group",
        "name": "test_api",
        "path": "/test/api",
        "method": "GET"
    }
    response = client.post(
        f"{settings.API_V1_STR}/apis/",
        headers=superuser_token_headers,
        json=data,
    )
    api_id = response.json()["id"]

    update_data = {
        "group": "updated_group",
        "name": "updated_api",
        "path": "/updated/api",
        "method": "POST"
    }
    response = client.put(
        f"{settings.API_V1_STR}/apis/{api_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["group"] == update_data["group"]
    assert content["name"] == update_data["name"]
    assert content["path"] == update_data["path"]
    assert content["method"] == update_data["method"]
    assert content["id"] == api_id

def test_delete_api(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "group": "test_group",
        "name": "test_api",
        "path": "/test/api",
        "method": "GET"
    }
    response = client.post(
        f"{settings.API_V1_STR}/apis/",
        headers=superuser_token_headers,
        json=data,
    )
    api_id = response.json()["id"]

    response = client.delete(
        f"{settings.API_V1_STR}/apis/{api_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
