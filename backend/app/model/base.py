import uuid
from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer
from sqlmodel import Field, SQLModel


def _utc_serializer(dt: datetime) -> str:
    """Serialize datetime to UTC ISO 8601 format"""
    # Return None if datetime is None
    if dt is None:
        return None
    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Convert to ISO 8601 format
    return dt.isoformat()


DateTime = Annotated[datetime, PlainSerializer(_utc_serializer)]


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    # Save user id in "sub" field
    sub: str | None = None
    type: str = "access"


class NewPassword(SQLModel):
    token: str
    new_password: str


class BaseDataModel(SQLModel):
    """Base data model with common fields"""

    # Primary Key
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        unique=True,
        index=True,
    )
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    deleted_at: datetime | None = Field(default=None, index=True, nullable=True)
