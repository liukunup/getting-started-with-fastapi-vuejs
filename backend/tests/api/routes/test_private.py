from fastapi.testclient import TestClient
from app.core.config import settings
from tests.utils import random_email, random_lower_string

def test_create_private_user(client: TestClient) -> None:
    email = random_email()
    password = random_lower_string()
    nickname = random_lower_string()
    data = {"email": email, "password": password, "nickname": nickname}
    
    r = client.post(f"{settings.API_V1_STR}/private/users/", json=data)
    assert r.status_code == 200
    content = r.json()
    assert content["email"] == email
    # assert content["nickname"] == nickname
    assert "id" in content
