from fastapi.testclient import TestClient
from app.core.config import settings
from tests.utils import random_email, random_lower_string
from unittest.mock import patch

def test_read_users(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/", headers=superuser_token_headers)
    assert r.status_code == 200
    result = r.json()
    assert result["total"] >= 1
    assert len(result["users"]) >= 1

def test_create_user(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "username": username}
    
    with patch("app.api.routes.user.send_email") as mock_send_email:
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 200
        created_user = r.json()
        assert created_user["email"] == username
        assert "id" in created_user

def test_read_user_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    assert r.status_code == 200
    current_user = r.json()
    assert current_user["email"] == settings.FIRST_SUPERUSER

def test_update_user_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    new_nickname = random_lower_string()
    data = {"nickname": new_nickname}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["nickname"] == new_nickname

def test_update_password_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    new_password = random_lower_string()
    data = {
        "old_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": new_password,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    assert "message" in r.json()
    
    # Revert password for other tests
    data_revert = {
        "old_password": new_password,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data_revert,
    )
    assert r.status_code == 200

def test_register_user(client: TestClient) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "username": username}
    
    r = client.post(f"{settings.API_V1_STR}/users/signup", json=data)
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == username
    assert "id" in created_user

def test_read_user_by_id(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "username": username}
    
    with patch("app.api.routes.user.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 200
        user_id = r.json()["id"]

    r = client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["email"] == username
    assert content["id"] == user_id

def test_update_user(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "username": username}
    
    with patch("app.api.routes.user.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        user_id = r.json()["id"]

    new_nickname = random_lower_string()
    update_data = {"nickname": new_nickname}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["nickname"] == new_nickname

def test_delete_user(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "username": username}
    
    with patch("app.api.routes.user.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        user_id = r.json()["id"]

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted successfully"
    
    r = client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404

def test_delete_user_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create a new user to delete
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "username": username}
    
    with patch("app.api.routes.user.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        user_id = r.json()["id"]
    
    # Login as the new user
    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted successfully"
    
    # Verify deletion
    r = client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404

def test_force_logout(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "username": username}
    
    with patch("app.api.routes.user.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        user_id = r.json()["id"]

    r = client.post(
        f"{settings.API_V1_STR}/users/{user_id}/force-logout",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "User forced to logout"
