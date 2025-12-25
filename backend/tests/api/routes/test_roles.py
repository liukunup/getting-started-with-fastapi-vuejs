import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.model.role import Role
from tests.utils import random_lower_string

def test_read_roles(
    client: TestClient, superuser_token_headers: dict[str, str], session: Session
) -> None:
    role = Role(name=random_lower_string(), description=random_lower_string())
    session.add(role)
    session.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/roles/", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert "roles" in content
    assert "total" in content
    assert len(content["roles"]) > 0

def test_create_role(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    name = random_lower_string()
    description = random_lower_string()
    data = {"name": name, "description": description}
    response = client.post(
        f"{settings.API_V1_STR}/roles/", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == name
    assert content["description"] == description
    assert "id" in content

def test_read_role(
    client: TestClient, superuser_token_headers: dict[str, str], session: Session
) -> None:
    role = Role(name=random_lower_string(), description=random_lower_string())
    session.add(role)
    session.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/roles/{role.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == role.name
    assert content["id"] == str(role.id)

def test_update_role(
    client: TestClient, superuser_token_headers: dict[str, str], session: Session
) -> None:
    role = Role(name=random_lower_string(), description=random_lower_string())
    session.add(role)
    session.commit()
    
    new_description = random_lower_string()
    data = {"description": new_description}
    response = client.put(
        f"{settings.API_V1_STR}/roles/{role.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["description"] == new_description
    assert content["name"] == role.name
