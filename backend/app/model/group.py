import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel
from .link import GroupMemberLink
from .user import UserPublic

if TYPE_CHECKING:
    from .user import User


class GroupBase(SQLModel):
    name: str = Field(max_length=255, nullable=False, index=True)
    description: str | None = Field(default=None, max_length=512)


class GroupCreate(GroupBase):
    owner_id: uuid.UUID | None = None
    member_ids: list[uuid.UUID] | None = []


class GroupUpdate(GroupBase):
    name: str | None = None
    owner_id: uuid.UUID | None = None
    member_ids: list[uuid.UUID] | None = None


class Group(GroupBase, BaseDataModel, table=True):
    __tablename__ = "groups"

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    owner: Optional["User"] = Relationship(back_populates="groups")

    members: list["User"] = Relationship(
        back_populates="group_members", link_model=GroupMemberLink
    )


class GroupPublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    owner: UserPublic | None = None
    members: list[UserPublic] | None = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GroupsPublic(SQLModel):
    groups: list[GroupPublic]
    total: int
