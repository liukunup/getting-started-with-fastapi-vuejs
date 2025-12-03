from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.crud import user as user_crud
from app.model.user import User, UserCreate, UserPrivate


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str | None = None


router = APIRouter(tags=["Private"], prefix="/private")


@router.post("/users/", response_model=UserPrivate)
def create_user(
    session: SessionDep,
    user_in: PrivateUserCreate,
) -> User:
    """
    Create a new user.
    """
    user_create = UserCreate(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
    )
    user = user_crud.create_user(session=session, user_create=user_create)
    return user
