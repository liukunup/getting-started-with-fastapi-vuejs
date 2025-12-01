import hashlib
import hmac
import time
import uuid
from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from redis import Redis
from sqlmodel import Session, select

from app.core import security
from app.core.cache import redis_client
from app.core.config import settings
from app.core.database import engine
from app.model.application import Application
from app.model.base import TokenPayload
from app.model.user import Role, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_cache() -> Generator[Redis, None, None]:
    yield redis_client


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]
CacheDep = Annotated[Redis, Depends(get_cache)]


def get_current_user(session: SessionDep, token: TokenDep, cache: CacheDep) -> User:  # type: ignore
    # Check blacklist
    if cache.get(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has been revoked",
        )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user = session.get(User, token_data.sub)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


CurrentUser = Annotated[User, Depends(get_current_user)]


def verify_openapi_signature(
    session: SessionDep,
    cache: CacheDep,
    x_app_id: str = Header(..., alias="X-App-Id", description="Application ID"),
    x_timestamp: int = Header(
        ..., alias="X-Timestamp", description="Timestamp in seconds"
    ),
    x_sign: str = Header(..., alias="X-Sign", description="Signature"),
    x_trace_id: str = Header(
        ..., alias="X-Trace-Id", description="Trace ID for tracking"
    ),
) -> Application:
    """
    Verify OpenAPI signature.
    Signature Rule: HMAC-SHA256(app_key, "app_id={x_app_id}&timestamp={x_timestamp}&trace_id={x_trace_id}")
    """
    # 1. Check Trace ID to prevent replay attacks
    trace_key = f"openapi:trace:{x_trace_id}"
    if cache.get(trace_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Replay attack detected",
        )

    # 2. Check timestamp (e.g., 15 minutes expiration)
    current_timestamp = int(time.time())
    if abs(current_timestamp - x_timestamp) > 900:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Timestamp expired",
        )

    # 3. Get App Key from DB
    try:
        app_uuid = uuid.UUID(x_app_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid App ID format",
        )

    statement = select(Application).where(Application.app_id == app_uuid)
    app = session.exec(statement).first()
    if not app or not app.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid App ID or App is inactive",
        )

    # 4. Verify Signature
    sign_str = f"app_id={x_app_id}&timestamp={x_timestamp}&trace_id={x_trace_id}"
    expected_sign = hmac.new(
        app.app_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sign, x_sign):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Signature",
        )

    # Cache Trace ID with expiration (900s matches timestamp window)
    cache.set(trace_key, "1", ex=900)

    return app


CurrentApp = Annotated[Application, Depends(verify_openapi_signature)]


def get_current_active_superuser(current_user: CurrentUser) -> User:  # type: ignore
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(
        self, session: SessionDep, current_user: User = Depends(get_current_user)
    ) -> bool:
        if current_user.is_superuser:
            return True

        # We need to ensure role and permissions are loaded
        # Since current_user might be detached or we want to be safe
        # Let's query the role permissions
        if not current_user.role_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        role = session.get(Role, current_user.role_id)
        if not role:
            raise HTTPException(status_code=403, detail="Role not found")

        # Assuming permissions are loaded or we check them
        # We need to load permissions for the role.
        # In SQLModel/SQLAlchemy, accessing role.permissions should trigger load if session is active
        permissions = [p.name for p in role.permissions]

        if self.required_permission not in permissions:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return True
