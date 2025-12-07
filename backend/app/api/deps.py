import hashlib
import hmac
import time
import uuid
from collections.abc import Generator
from typing import Annotated

import jwt
from celery import Celery
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from app.celery.celery import celery_app
from app.core import security
from app.core.cache import Cache, cache
from app.core.config import settings
from app.core.database import engine
from app.core.storage import Storage, storage
from app.model.application import Application
from app.model.base import TokenPayload
from app.model.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_cache() -> Generator[Cache, None, None]:
    yield cache


def get_storage() -> Generator[Storage, None, None]:
    yield storage


def get_celery_app() -> Generator[Celery, None, None]:
    yield celery_app


TokenDep = Annotated[str, Depends(reusable_oauth2)]
SessionDep = Annotated[Session, Depends(get_db)]
CacheDep = Annotated[Cache, Depends(get_cache)]
StorageDep = Annotated[Storage, Depends(get_storage)]
CeleryDep = Annotated[Celery, Depends(get_celery_app)]


def get_current_user(session: SessionDep, token: TokenDep, cache: CacheDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user_id = uuid.UUID(token_data.sub)

        if cache.redis.get(f"blacklist:user:{user_id}"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User forced logout"
            )

        statement = (
            select(User).where(User.id == user_id).options(joinedload(User.role))
        )
        user = session.exec(statement).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )
        return user
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def verify_openapi_signature(
    session: SessionDep,
    cache: CacheDep,
    x_app_id: str = Header(..., alias="X-App-Id"),
    x_timestamp: int = Header(..., alias="X-Timestamp"),
    x_sign: str = Header(..., alias="X-Sign"),
    x_trace_id: str = Header(..., alias="X-Trace-Id"),
) -> Application:
    """
    Verify OpenAPI signature.
    Signature Rule: HMAC-SHA256(app_key, "app_id={x_app_id}&timestamp={x_timestamp}&trace_id={x_trace_id}")
    """
    # 1. Check Trace ID to prevent replay attacks
    trace_key = f"openapi:trace:{x_trace_id}"
    if cache.redis.get(trace_key):
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
    cache.redis.set(trace_key, "1", ex=900)

    return app


CurrentApp = Annotated[Application, Depends(verify_openapi_signature)]
