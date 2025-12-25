import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.model.menu import Menu
from tests.utils import random_lower_string

def test_read_menus(
    client: TestClient, superuser_token_headers: dict[str, str], session: Session
) -> None:
    menu = Menu(
        name=random_lower_string(),
        label=random_lower_string(),
        path=f"/{random_lower_string()}",
        component=random_lower_string(),
        sort=1
    )
    session.add(menu)
    session.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/menus/", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, list)
    # Since the response is a tree, we might need to traverse or just check if it's a list
    # Assuming at least one menu exists (the one we created or seeded)

def test_create_menu(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    name = random_lower_string()
    label = random_lower_string()
    path = f"/{random_lower_string()}"
    component = random_lower_string()
    data = {
        "name": name,
        "label": label,
        "path": path,
        "component": component,
        "sort": 10,
        "icon": "pi pi-home",
        "is_hidden": False
    }
    response = client.post(
        f"{settings.API_V1_STR}/menus/", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == name
    assert content["label"] == label
    assert "id" in content

def test_read_menu(
    client: TestClient, superuser_token_headers: dict[str, str], session: Session
) -> None:
    menu = Menu(
        name=random_lower_string(),
        label=random_lower_string(),
        path=f"/{random_lower_string()}",
        component=random_lower_string(),
        sort=1
    )
    session.add(menu)
    session.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/menus/{menu.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == menu.name
    assert content["id"] == str(menu.id)

def test_update_menu(
    client: TestClient, superuser_token_headers: dict[str, str], session: Session
) -> None:
    menu = Menu(
        name=random_lower_string(),
        label=random_lower_string(),
        path=f"/{random_lower_string()}",
        component=random_lower_string(),
        sort=1
    )
    session.add(menu)
    session.commit()
    
    new_label = random_lower_string()
    data = {"label": new_label}
    response = client.put(
        f"{settings.API_V1_STR}/menus/{menu.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["label"] == new_label
    assert content["name"] == menu.name

def test_delete_menu(
    client: TestClient, superuser_token_headers: dict[str, str], session: Session
) -> None:
    menu = Menu(
        name=random_lower_string(),
        label=random_lower_string(),
        path=f"/{random_lower_string()}",
        component=random_lower_string(),
        sort=1
    )
    session.add(menu)
    session.commit()
    
    response = client.delete(
        f"{settings.API_V1_STR}/menus/{menu.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Menu deleted successfully"
    
    response = client.get(
        f"{settings.API_V1_STR}/menus/{menu.id}", headers=superuser_token_headers
    )
    assert response.status_code == 404
