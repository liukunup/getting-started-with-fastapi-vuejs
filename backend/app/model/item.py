import uuid
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel, DateTime
from .user import UserPublic

if TYPE_CHECKING:
    from .user import User


class ItemBase(SQLModel):
    name: str = Field(max_length=255, nullable=False, index=True)
    description: str | None = Field(default=None, max_length=512)


class ItemCreate(ItemBase):
    owner_id: uuid.UUID | None = None


class ItemUpdate(ItemBase):
    name: str | None = None
    owner_id: uuid.UUID | None = None


class Item(ItemBase, BaseDataModel, table=True):
    __tablename__ = "items"

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    owner: Optional["User"] = Relationship(back_populates="items")


class ItemPublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    owner: UserPublic | None = None
    created_at: DateTime | None = None
    updated_at: DateTime | None = None


class ItemsPublic(SQLModel):
    items: list[ItemPublic]
    total: int
