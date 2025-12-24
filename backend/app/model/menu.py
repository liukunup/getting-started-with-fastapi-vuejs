import uuid
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel

if TYPE_CHECKING:
    from .user import User


class MenuBase(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    path: str | None = Field(default=None, max_length=255)
    component: str | None = Field(default=None, max_length=255)
    label: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=255)
    to: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=255)
    target: str | None = Field(default=None, max_length=255)
    clazz: str | None = Field(default=None, max_length=255)
    is_hidden: bool = Field(default=False)
    sort: int = Field(default=0)
    parent_id: uuid.UUID | None = Field(default=None)


class MenuCreate(MenuBase):
    pass


class MenuUpdate(MenuBase):
    is_hidden: bool | None = Field(default=None)
    sort: int | None = Field(default=None)


class Menu(MenuBase, BaseDataModel, table=True):
    __tablename__ = "menus"

    parent_id: uuid.UUID | None = Field(default=None, foreign_key="menus.id")
    parent: "Menu" = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Menu.id"}
    )
    children: list["Menu"] = Relationship(back_populates="parent")

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    owner: Optional["User"] = Relationship(back_populates="menus")


class MenuTreeNode(SQLModel):
    id: uuid.UUID
    name: str | None = None
    path: str | None = None
    component: str | None = None
    label: str | None = None
    icon: str | None = None
    to: str | None = None
    url: str | None = None
    target: str | None = None
    clazz: str | None = None
    is_hidden: bool
    sort: int
    parent_id: uuid.UUID | None = None
    items: list["MenuTreeNode"] | None = None
    children: list["MenuTreeNode"] | None = None
    roles: list[str] | None = None


class MenuTreePublic(SQLModel):
    data: list[MenuTreeNode]
    total: int
