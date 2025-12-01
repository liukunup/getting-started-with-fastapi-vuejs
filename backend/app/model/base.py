import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Message(SQLModel):
    message: str


class Task(SQLModel):
    task_id: str
    message: str


class Token(SQLModel):
    access_token: str


class TokenPayload(SQLModel):
    # Save user id in "sub" field
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str


class BaseDataModel(SQLModel):
    # Common fields for all data models
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
