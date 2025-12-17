from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlmodel import Session, select

from app.api.deps import SessionDep, get_current_active_superuser
from app.core.config import settings
from app.model.system_setting import SystemSetting

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsUpdate(BaseModel):
    # General
    PROJECT_NAME: str | None = None

    # Sentry
    SENTRY_DSN: HttpUrl | str | None = None

    # Email
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool | None = None
    SMTP_SSL: bool | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    # OpenID Connect
    OIDC_ENABLED: bool | None = None
    OIDC_NAME: str | None = None
    OIDC_AUTH_URL: str | None = None
    OIDC_TOKEN_URL: str | None = None
    OIDC_USERINFO_URL: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_CLIENT_SECRET: str | None = None
    OIDC_SCOPES: str | None = None
    SIGNOUT_REDIRECT_URL: str | None = None
    AUTO_LOGIN: bool | None = None

    # LDAP
    LDAP_ENABLED: bool | None = None
    LDAP_HOST: str | None = None
    LDAP_PORT: int | None = None
    LDAP_BIND_DN: str | None = None
    LDAP_BIND_PASSWORD: str | None = None
    LDAP_BASE_DN: str | None = None
    LDAP_USER_FILTER: str | None = None
    LDAP_EMAIL_ATTRIBUTE: str | None = None
    LDAP_USERNAME_ATTRIBUTE: str | None = None
    LDAP_FULLNAME_ATTRIBUTE: str | None = None


def _update_setting(
    session: Session, key: str, current_value: str | None, new_value: str | None = None
):
    if new_value is not None and new_value != current_value:
        # Only update if the value has changed
        current_value = new_value
        # Upsert the setting in the DB
        setting = session.get(SystemSetting, key)
        if not setting:
            setting = SystemSetting(key=key, value=current_value)
            session.add(setting)
        else:
            setting.value = current_value
            session.add(setting)


@router.get("/", dependencies=[Depends(get_current_active_superuser)], summary="Retrieve system settings")
def get_settings(session: SessionDep):
    # Try to load from DB first to ensure we have the latest
    # Note: In a real production app with high traffic, you might want to cache this
    # or only load on startup/change. For this admin panel, reading from DB is fine.
    db_settings = session.exec(select(SystemSetting)).all()
    settings_map = {s.key: s.value for s in db_settings}

    # Helper to get value from DB or fallback to current settings (env/default)
    def get_val(key, default):
        return settings_map.get(key, default)

    return {
        # General
        "PROJECT_NAME": get_val("PROJECT_NAME", settings.PROJECT_NAME),
        # Sentry
        "SENTRY_DSN": get_val(
            "SENTRY_DSN", str(settings.SENTRY_DSN) if settings.SENTRY_DSN else None
        ),
        # Email
        "SMTP_HOST": get_val("SMTP_HOST", settings.SMTP_HOST),
        "SMTP_PORT": int(get_val("SMTP_PORT", settings.SMTP_PORT))
        if get_val("SMTP_PORT", settings.SMTP_PORT)
        else None,
        "SMTP_USER": get_val("SMTP_USER", settings.SMTP_USER),
        # Do not return password for security
        "EMAILS_FROM_EMAIL": get_val("EMAILS_FROM_EMAIL", settings.EMAILS_FROM_EMAIL),
        "EMAILS_FROM_NAME": get_val("EMAILS_FROM_NAME", settings.EMAILS_FROM_NAME),
        "SMTP_TLS": get_val("SMTP_TLS", settings.SMTP_TLS) == "True"
        if "SMTP_TLS" in settings_map
        else settings.SMTP_TLS,
        "SMTP_SSL": get_val("SMTP_SSL", settings.SMTP_SSL) == "True"
        if "SMTP_SSL" in settings_map
        else settings.SMTP_SSL,
        # OIDC
        "OIDC_ENABLED": get_val("OIDC_ENABLED", settings.OIDC_ENABLED) == "True"
        if "OIDC_ENABLED" in settings_map
        else settings.OIDC_ENABLED,
        "OIDC_NAME": get_val("OIDC_NAME", settings.OIDC_NAME),
        "OIDC_AUTH_URL": get_val("OIDC_AUTH_URL", settings.OIDC_AUTH_URL),
        "OIDC_TOKEN_URL": get_val("OIDC_TOKEN_URL", settings.OIDC_TOKEN_URL),
        "OIDC_USERINFO_URL": get_val("OIDC_USERINFO_URL", settings.OIDC_USERINFO_URL),
        "OIDC_CLIENT_ID": get_val("OIDC_CLIENT_ID", settings.OIDC_CLIENT_ID),
        # Do not return secret for security
        "OIDC_SCOPES": get_val("OIDC_SCOPES", settings.OIDC_SCOPES),
        "SIGNOUT_REDIRECT_URL": get_val(
            "SIGNOUT_REDIRECT_URL", settings.SIGNOUT_REDIRECT_URL
        ),
        "AUTO_LOGIN": get_val("AUTO_LOGIN", settings.AUTO_LOGIN) == "True"
        if "AUTO_LOGIN" in settings_map
        else settings.AUTO_LOGIN,
        # LDAP
        "LDAP_ENABLED": get_val("LDAP_ENABLED", settings.LDAP_ENABLED) == "True"
        if "LDAP_ENABLED" in settings_map
        else settings.LDAP_ENABLED,
        "LDAP_HOST": get_val("LDAP_HOST", settings.LDAP_HOST),
        "LDAP_PORT": int(get_val("LDAP_PORT", settings.LDAP_PORT))
        if get_val("LDAP_PORT", settings.LDAP_PORT)
        else None,
        "LDAP_BIND_DN": get_val("LDAP_BIND_DN", settings.LDAP_BIND_DN),
        # Do not return password for security
        "LDAP_BASE_DN": get_val("LDAP_BASE_DN", settings.LDAP_BASE_DN),
        "LDAP_USER_FILTER": get_val("LDAP_USER_FILTER", settings.LDAP_USER_FILTER),
        "LDAP_EMAIL_ATTRIBUTE": get_val(
            "LDAP_EMAIL_ATTRIBUTE", settings.LDAP_EMAIL_ATTRIBUTE
        ),
        "LDAP_USERNAME_ATTRIBUTE": get_val(
            "LDAP_USERNAME_ATTRIBUTE", settings.LDAP_USERNAME_ATTRIBUTE
        ),
        "LDAP_FULLNAME_ATTRIBUTE": get_val(
            "LDAP_FULLNAME_ATTRIBUTE", settings.LDAP_FULLNAME_ATTRIBUTE
        ),
    }


@router.post("/", dependencies=[Depends(get_current_active_superuser)], summary="Update system settings")
def update_settings(session: SessionDep, new_settings: SettingsUpdate):
    # General
    _update_setting(
        session, "PROJECT_NAME", settings.PROJECT_NAME, new_settings.PROJECT_NAME
    )

    # Sentry
    _update_setting(
        session,
        "SENTRY_DSN",
        str(settings.SENTRY_DSN) if settings.SENTRY_DSN else None,
        new_settings.SENTRY_DSN,
    )

    # Email
    _update_setting(session, "SMTP_HOST", settings.SMTP_HOST, new_settings.SMTP_HOST)
    _update_setting(
        session,
        "SMTP_PORT",
        str(settings.SMTP_PORT) if settings.SMTP_PORT else None,
        str(new_settings.SMTP_PORT) if new_settings.SMTP_PORT else None,
    )
    _update_setting(session, "SMTP_USER", settings.SMTP_USER, new_settings.SMTP_USER)
    _update_setting(
        session, "SMTP_PASSWORD", settings.SMTP_PASSWORD, new_settings.SMTP_PASSWORD
    )
    _update_setting(
        session,
        "SMTP_TLS",
        str(settings.SMTP_TLS) if settings.SMTP_TLS else None,
        str(new_settings.SMTP_TLS) if new_settings.SMTP_TLS else None,
    )
    _update_setting(
        session,
        "SMTP_SSL",
        str(settings.SMTP_SSL) if settings.SMTP_SSL else None,
        str(new_settings.SMTP_SSL) if new_settings.SMTP_SSL else None,
    )
    _update_setting(
        session,
        "EMAILS_FROM_EMAIL",
        str(settings.EMAILS_FROM_EMAIL) if settings.EMAILS_FROM_EMAIL else None,
        str(new_settings.EMAILS_FROM_EMAIL) if new_settings.EMAILS_FROM_EMAIL else None,
    )
    _update_setting(
        session,
        "EMAILS_FROM_NAME",
        settings.EMAILS_FROM_NAME,
        new_settings.EMAILS_FROM_NAME,
    )

    # OIDC
    _update_setting(
        session,
        "OIDC_ENABLED",
        str(settings.OIDC_ENABLED) if settings.OIDC_ENABLED else None,
        str(new_settings.OIDC_ENABLED)
        if new_settings.OIDC_ENABLED is not None
        else None,
    )
    _update_setting(session, "OIDC_NAME", settings.OIDC_NAME, new_settings.OIDC_NAME)
    _update_setting(
        session,
        "OIDC_AUTH_URL",
        settings.OIDC_AUTH_URL,
        new_settings.OIDC_AUTH_URL,
    )
    _update_setting(
        session,
        "OIDC_TOKEN_URL",
        settings.OIDC_TOKEN_URL,
        new_settings.OIDC_TOKEN_URL,
    )
    _update_setting(
        session,
        "OIDC_USERINFO_URL",
        settings.OIDC_USERINFO_URL,
        new_settings.OIDC_USERINFO_URL,
    )
    _update_setting(
        session, "OIDC_CLIENT_ID", settings.OIDC_CLIENT_ID, new_settings.OIDC_CLIENT_ID
    )
    _update_setting(
        session,
        "OIDC_CLIENT_SECRET",
        settings.OIDC_CLIENT_SECRET,
        new_settings.OIDC_CLIENT_SECRET,
    )
    _update_setting(
        session, "OIDC_SCOPES", settings.OIDC_SCOPES, new_settings.OIDC_SCOPES
    )
    _update_setting(
        session,
        "SIGNOUT_REDIRECT_URL",
        settings.SIGNOUT_REDIRECT_URL,
        new_settings.SIGNOUT_REDIRECT_URL,
    )
    _update_setting(
        session,
        "AUTO_LOGIN",
        str(settings.AUTO_LOGIN) if settings.AUTO_LOGIN else None,
        str(new_settings.AUTO_LOGIN) if new_settings.AUTO_LOGIN is not None else None,
    )

    # LDAP
    _update_setting(
        session,
        "LDAP_ENABLED",
        str(settings.LDAP_ENABLED) if settings.LDAP_ENABLED else None,
        str(new_settings.LDAP_ENABLED)
        if new_settings.LDAP_ENABLED is not None
        else None,
    )
    _update_setting(session, "LDAP_HOST", settings.LDAP_HOST, new_settings.LDAP_HOST)
    _update_setting(
        session,
        "LDAP_PORT",
        str(settings.LDAP_PORT) if settings.LDAP_PORT else None,
        str(new_settings.LDAP_PORT) if new_settings.LDAP_PORT else None,
    )
    _update_setting(
        session, "LDAP_BIND_DN", settings.LDAP_BIND_DN, new_settings.LDAP_BIND_DN
    )
    _update_setting(
        session,
        "LDAP_BIND_PASSWORD",
        settings.LDAP_BIND_PASSWORD,
        new_settings.LDAP_BIND_PASSWORD,
    )
    _update_setting(
        session, "LDAP_BASE_DN", settings.LDAP_BASE_DN, new_settings.LDAP_BASE_DN
    )
    _update_setting(
        session,
        "LDAP_USER_FILTER",
        settings.LDAP_USER_FILTER,
        new_settings.LDAP_USER_FILTER,
    )
    _update_setting(
        session,
        "LDAP_EMAIL_ATTRIBUTE",
        settings.LDAP_EMAIL_ATTRIBUTE,
        new_settings.LDAP_EMAIL_ATTRIBUTE,
    )
    _update_setting(
        session,
        "LDAP_USERNAME_ATTRIBUTE",
        settings.LDAP_USERNAME_ATTRIBUTE,
        new_settings.LDAP_USERNAME_ATTRIBUTE,
    )
    _update_setting(
        session,
        "LDAP_FULLNAME_ATTRIBUTE",
        settings.LDAP_FULLNAME_ATTRIBUTE,
        new_settings.LDAP_FULLNAME_ATTRIBUTE,
    )

    session.commit()

    return {"message": "Settings updated successfully"}
