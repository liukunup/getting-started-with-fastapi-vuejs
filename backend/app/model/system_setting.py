from sqlmodel import Field, SQLModel


class SystemSetting(SQLModel, table=True):
    __tablename__ = "system_settings"

    # Save system settings as key-value pairs
    key: str = Field(primary_key=True, nullable=False, unique=True, index=True)
    value: str | None = None
