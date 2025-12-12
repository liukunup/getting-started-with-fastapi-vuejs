import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    MariaDBDsn,
    MySQLDsn,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = secrets.token_urlsafe(32)

    # 60 minutes * 24 hours * 30 days = 30 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    FRONTEND_HOST: str = "http://localhost:5173"

    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str

    SENTRY_DSN: HttpUrl | None = None

    GRAVATAR_SOURCE: HttpUrl = "https://cravatar.cn/avatar/"

    # Database
    DATABASE_TYPE: Literal["sqlite", "mysql", "mariadb", "postgres"] = "postgres"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "myapp"
    DATABASE_PASSWORD: str = "changethis"
    DATABASE_NAME: str = "myapp"

    # SQLite
    SQLITE_FILE: str = "myapp.db"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn | MySQLDsn | MariaDBDsn | str:
        if self.DATABASE_TYPE == "sqlite":
            return f"sqlite:///{self.SQLITE_FILE}"

        if self.DATABASE_TYPE == "mysql":
            return MySQLDsn.build(
                scheme="mysql+pymysql",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT or 3306,
                path=self.DATABASE_NAME,
            )

        if self.DATABASE_TYPE == "mariadb":
            return MariaDBDsn.build(
                scheme="mariadb+mariadbconnector",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT or 3306,
                path=self.DATABASE_NAME,
            )

        if self.DATABASE_TYPE == "postgres":
            return PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT or 5432,
                path=self.DATABASE_NAME,
            )

        raise ValueError(f"Unknown database type: {self.DATABASE_TYPE}")

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URI(self) -> str:
        redis_url_postfix = f"{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{redis_url_postfix}"
        return f"redis://{redis_url_postfix}"

    # Storage
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "admin"
    STORAGE_SECRET_KEY: str = "changethis"
    STORAGE_BUCKET_NAME: str = "myapp"
    STORAGE_SECURE: bool = False

    # Email
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None
    EMAIL_TEST_USER: EmailStr = "test@example.com"

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 24

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # OIDC
    OIDC_ENABLED: bool = False
    OIDC_NAME: str | None = None
    OIDC_AUTH_URL: str | None = None
    OIDC_TOKEN_URL: str | None = None
    OIDC_USERINFO_URL: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_CLIENT_SECRET: str | None = None
    OIDC_SCOPES: str = "openid profile email"
    SIGNOUT_REDIRECT_URL: str | None = None
    AUTO_LOGIN: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def oidc_configured(self) -> bool:
        return (
            self.OIDC_AUTH_URL is not None
            and self.OIDC_TOKEN_URL is not None
            and self.OIDC_USERINFO_URL is not None
            and self.OIDC_CLIENT_ID is not None
            and self.OIDC_CLIENT_SECRET is not None
            and self.OIDC_SCOPES is not None
        )

    # LDAP
    LDAP_ENABLED: bool = False
    LDAP_HOST: str | None = None
    LDAP_PORT: int = 389
    LDAP_BIND_DN: str | None = None
    LDAP_BIND_PASSWORD: str | None = None
    LDAP_BASE_DN: str | None = None
    LDAP_USER_FILTER: str = "(cn={username})"
    LDAP_EMAIL_ATTRIBUTE: str = "mail"
    LDAP_USERNAME_ATTRIBUTE: str = "cn"
    LDAP_FULLNAME_ATTRIBUTE: str = "displayName"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ldap_configured(self) -> bool:
        return (
            self.LDAP_HOST is not None
            and self.LDAP_BIND_DN is not None
            and self.LDAP_BIND_PASSWORD is not None
        )

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
