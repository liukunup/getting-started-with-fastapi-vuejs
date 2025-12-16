import uuid
from collections.abc import Generator
from typing import Annotated

import jwt
from celery import Celery
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from app.worker.celery import celery_app
from app.core import security
from app.core.cache import Cache, cache
from app.core.config import settings
from app.core.database import engine
from app.core.storage import Storage, storage
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
