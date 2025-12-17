import secrets
import uuid
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseDataModel, DateTime
from .user import UserPublic

if TYPE_CHECKING:
    from .user import User


class ApplicationBase(SQLModel):
    name: str = Field(max_length=255, nullable=False, index=True)
    description: str | None = Field(default=None, max_length=512)
    is_active: bool = Field(default=True)


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(ApplicationBase):
    name: str | None = None
    is_active: bool | None = None


class Application(ApplicationBase, BaseDataModel, table=True):
    __tablename__ = "applications"

    app_id: uuid.UUID = Field(
        default_factory=uuid.uuid4, unique=True, nullable=False, index=True
    )
    app_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32), nullable=False
    )

    owner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    owner: Optional["User"] = Relationship(back_populates="applications")


class ApplicationPublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    is_active: bool
    app_id: uuid.UUID
    owner: UserPublic | None = None
    created_at: DateTime | None = None
    updated_at: DateTime | None = None


class ApplicationsPublic(SQLModel):
    applications: list[ApplicationPublic]
    total: int


class ApplicationPrivate(ApplicationPublic):
    app_key: str


class ApplicationsPrivate(SQLModel):
    applications: list[ApplicationPrivate]
    total: int
