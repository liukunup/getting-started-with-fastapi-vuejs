import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel
from .link import GroupMemberLink

if TYPE_CHECKING:
    from .application import Application
    from .group import Group
    from .item import Item
    from .task import Task


class RolePermissionLink(SQLModel, table=True):
    __tablename__ = "role_permission_link"

    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True)
    permission_id: uuid.UUID = Field(foreign_key="permissions.id", primary_key=True)


class Permission(BaseDataModel, table=True):
    __tablename__ = "permissions"

    name: str = Field(max_length=255, nullable=False, unique=True, index=True)
    description: str | None = Field(default=None, max_length=512)
    roles: list["Role"] = Relationship(
        back_populates="permissions", link_model=RolePermissionLink
    )


class Role(BaseDataModel, table=True):
    __tablename__ = "roles"

    name: str = Field(max_length=255, nullable=False, unique=True, index=True)
    description: str | None = Field(default=None, max_length=512)
    permissions: list["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermissionLink
    )
    users: list["User"] = Relationship(back_populates="role")


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

    role_id: uuid.UUID | None = Field(default=None, foreign_key="roles.id")
    role: Role | None = Relationship(back_populates="users")

    items: list["Item"] = Relationship(back_populates="owner")
    applications: list["Application"] = Relationship(back_populates="owner")
    tasks: list["Task"] = Relationship(back_populates="owner")
    groups: list["Group"] = Relationship(back_populates="owner")
    group_members: list["Group"] = Relationship(
        back_populates="members", link_model=GroupMemberLink
    )


class RolePublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None


class UserPublic(SQLModel):
    id: uuid.UUID
    username: str
    full_name: str | None = None
    avatar: str | None = None
    role: RolePublic | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
