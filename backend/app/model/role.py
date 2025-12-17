import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel, DateTime

if TYPE_CHECKING:
    from .user import User


class RoleBase(SQLModel):
    name: str = Field(max_length=255, nullable=False, unique=True, index=True)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    name: str | None = Field(default=None, max_length=255)


class Role(RoleBase, BaseDataModel, table=True):
    __tablename__ = "roles"

    users: list["User"] = Relationship(back_populates="role")


class RolePublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    created_at: DateTime | None = None
    updated_at: DateTime | None = None


class RolesPublic(SQLModel):
    roles: list[RolePublic]
    total: int
