import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel, DateTime
from .user import UserPublic

if TYPE_CHECKING:
    from .user import User


class ApiBase(SQLModel):
    group: str = Field(default="default", max_length=255, nullable=False, index=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    path: str = Field(max_length=255, nullable=False, index=True)
    method: str = Field(max_length=10, nullable=False, index=True)


class ApiCreate(ApiBase):
    pass


class ApiUpdate(ApiBase):
    group: str | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, max_length=255)
    path: str | None = Field(default=None, max_length=255)
    method: str | None = Field(default=None, max_length=10)


class Api(ApiBase, BaseDataModel, table=True):
    __tablename__ = "apis"

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    owner: Optional["User"] = Relationship(back_populates="apis")


class ApiPublic(SQLModel):
    id: uuid.UUID
    group: str
    name: str
    path: str
    method: str
    owner: UserPublic | None = None
    created_at: DateTime | None = None
    updated_at: DateTime | None = None


class ApiTreeNode(SQLModel):
    key: str
    data: Dict[str, Any]
    children: List["ApiTreeNode"] = Field(default_factory=list)


class ApisTreePublic(SQLModel):
    data: List[ApiTreeNode]
    total: int
