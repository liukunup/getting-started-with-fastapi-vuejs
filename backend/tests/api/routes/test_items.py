from fastapi.testclient import TestClient
from app.core.config import settings
from tests.utils import random_lower_string

def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert "id" in content
    # assert "owner_id" in content

def test_read_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    item_id = response.json()["id"]

    response = client.get(
        f"{settings.API_V1_STR}/items/{item_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["id"] == item_id

def test_read_items(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Foo", "description": "Fighters"}
    client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["items"]) >= 1
    assert content["total"] >= 1

def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    item_id = response.json()["id"]

    update_data = {"name": "Bar", "description": "Tenders"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == update_data["name"]
    assert content["description"] == update_data["description"]
    assert content["id"] == item_id

def test_delete_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    item_id = response.json()["id"]

    response = client.delete(
        f"{settings.API_V1_STR}/items/{item_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Item deleted successfully"

    response = client.get(
        f"{settings.API_V1_STR}/items/{item_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
