import uuid
from typing import TYPE_CHECKING

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel, DateTime
from .link import GroupMemberLink
from .role import Role, RolePublic

if TYPE_CHECKING:
    from .api import Api
    from .application import Application
    from .group import Group
    from .item import Item
    from .menu import Menu
    from .task import Task


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserBase(SQLModel):
    email: EmailStr = Field(max_length=255, unique=True, index=True)
    username: str = Field(max_length=255, unique=True, index=True)
    full_name: str | None = Field(default=None, max_length=255)
    avatar: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class UserCreate(UserBase):
    username: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role_id: uuid.UUID | None = None


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
    is_superuser: bool | None = None
    role_id: uuid.UUID | None = None


class UserUpdateMe(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    avatar: str | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, BaseDataModel, table=True):
    __tablename__ = "users"

    hashed_password: str

    # OpenID Connect subject identifier
    oidc_sub: str | None = Field(default=None, index=True)

    role_id: uuid.UUID | None = Field(default=None, foreign_key="roles.id")
    role: Role | None = Relationship(back_populates="users")

    apis: list["Api"] = Relationship(back_populates="owner")
    menus: list["Menu"] = Relationship(back_populates="owner")

    items: list["Item"] = Relationship(back_populates="owner")
    applications: list["Application"] = Relationship(back_populates="owner")
    tasks: list["Task"] = Relationship(back_populates="owner")
    groups: list["Group"] = Relationship(back_populates="owner")
    group_members: list["Group"] = Relationship(
        back_populates="members", link_model=GroupMemberLink
    )


class UserPublic(SQLModel):
    id: uuid.UUID
    username: str
    full_name: str | None = None
    avatar: str | None = None
    role: RolePublic | None = None
    created_at: DateTime | None = None
    updated_at: DateTime | None = None

    @field_validator("avatar", mode="after")
    @classmethod
    def sign_avatar_url(cls, v: str | None) -> str | None:
        if v and v.startswith("http"):
            return v

        from app.core.storage import storage

        return storage.get_presigned_url(v)


class UsersPublic(SQLModel):
    users: list[UserPublic]
    total: int


class UserPrivate(UserPublic):
    email: EmailStr
    username: str
    is_active: bool
    is_superuser: bool


class UsersPrivate(SQLModel):
    users: list[UserPrivate]
    total: int
