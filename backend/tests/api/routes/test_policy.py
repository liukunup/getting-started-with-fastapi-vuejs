from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.core.config import settings
from tests.utils import random_lower_string

def test_read_policies(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Mock enforcer.get_policy to return a list
    with patch("app.api.routes.policy.enforcer") as mock_enforcer:
        mock_enforcer.get_policy.return_value = []
        response = client.get(
            f"{settings.API_V1_STR}/policies/", headers=superuser_token_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

def test_add_and_remove_policy(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    sub = random_lower_string()
    obj = random_lower_string()
    act = "read"
    data = {"sub": sub, "obj": obj, "act": act}
    
    # Mock enforcer
    with patch("app.api.routes.policy.enforcer") as mock_enforcer:
        # Setup state for mock
        policies = []
        
        def add_policy(s, o, a):
            policies.append([s, o, a])
            return True
            
        def get_policy():
            return policies
            
        def remove_policy(s, o, a):
            if [s, o, a] in policies:
                policies.remove([s, o, a])
                return True
            return False

        mock_enforcer.add_policy.side_effect = add_policy
        mock_enforcer.get_policy.side_effect = get_policy
        mock_enforcer.remove_policy.side_effect = remove_policy

        # Add
        response = client.post(
            f"{settings.API_V1_STR}/policies/", headers=superuser_token_headers, json=data
        )
        assert response.status_code == 200
        assert response.json() is True
    
        # Verify added
        response = client.get(
            f"{settings.API_V1_STR}/policies/", headers=superuser_token_headers
        )
        policies_resp = response.json()
        assert any(p["sub"] == sub and p["obj"] == obj and p["act"] == act for p in policies_resp)
        
        # Remove
        response = client.request(
            "DELETE",
            f"{settings.API_V1_STR}/policies/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 200
    assert response.json() is True
    
    # Verify removed
    response = client.get(
        f"{settings.API_V1_STR}/policies/", headers=superuser_token_headers
    )
    policies = response.json()
    assert not any(p["sub"] == sub and p["obj"] == obj and p["act"] == act for p in policies)
