from fastapi.testclient import TestClient
from app.core.config import settings
from tests.utils import random_email, random_lower_string

def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]

def test_use_access_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=superuser_token_headers
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result

def test_password_recovery(client: TestClient) -> None:
    # Mock redis and email sending is handled in conftest or we can mock here if needed
    # But since we mocked redis in conftest, it should be fine.
    # We need to mock send_email though.
    from unittest.mock import patch
    
    with patch("app.api.routes.login.send_email") as mock_send_email:
        r = client.post(
            f"{settings.API_V1_STR}/login/password-recovery/{settings.FIRST_SUPERUSER}",
        )
        assert r.status_code == 200
        assert "message" in r.json()
        assert mock_send_email.called

def test_reset_password(client: TestClient) -> None:
    # This is tricky because we need a valid token.
    # We can generate one using the utility function.
    from app.utils import generate_reset_password_token
    
    token = generate_reset_password_token(email=settings.FIRST_SUPERUSER)
    new_password = random_lower_string()
    
    r = client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": new_password},
    )
    assert r.status_code == 200
    assert "message" in r.json()
