from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlmodel import Session, select

from app.api.deps import get_current_active_superuser, SessionDep
from app.core.config import settings
from app.model.system_setting import SystemSetting

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdate(BaseModel):
    PROJECT_NAME: str | None = None
    SENTRY_DSN: HttpUrl | str | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None
    SMTP_TLS: bool | None = None
    SMTP_SSL: bool | None = None
    SMTP_PORT: int | None = None

def _update_setting(session: Session, key: str, value: str):
    setting = session.get(SystemSetting, key)
    if not setting:
        setting = SystemSetting(key=key, value=value)
        session.add(setting)
    else:
        setting.value = value
        session.add(setting)

@router.get("/", dependencies=[Depends(get_current_active_superuser)])
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
        "PROJECT_NAME": get_val("PROJECT_NAME", settings.PROJECT_NAME),
        "SENTRY_DSN": get_val("SENTRY_DSN", str(settings.SENTRY_DSN) if settings.SENTRY_DSN else None),
        "SMTP_HOST": get_val("SMTP_HOST", settings.SMTP_HOST),
        "SMTP_USER": get_val("SMTP_USER", settings.SMTP_USER),
        # Do not return password for security
        "EMAILS_FROM_EMAIL": get_val("EMAILS_FROM_EMAIL", settings.EMAILS_FROM_EMAIL),
        "EMAILS_FROM_NAME": get_val("EMAILS_FROM_NAME", settings.EMAILS_FROM_NAME),
        "SMTP_TLS": get_val("SMTP_TLS", settings.SMTP_TLS) == "True" if "SMTP_TLS" in settings_map else settings.SMTP_TLS,
        "SMTP_SSL": get_val("SMTP_SSL", settings.SMTP_SSL) == "True" if "SMTP_SSL" in settings_map else settings.SMTP_SSL,
        "SMTP_PORT": int(get_val("SMTP_PORT", settings.SMTP_PORT)) if get_val("SMTP_PORT", settings.SMTP_PORT) else None,
    }

@router.post("/", dependencies=[Depends(get_current_active_superuser)])
def update_settings(new_settings: SettingsUpdate, session: SessionDep):
    if new_settings.PROJECT_NAME is not None:
        settings.PROJECT_NAME = new_settings.PROJECT_NAME
        _update_setting(session, "PROJECT_NAME", new_settings.PROJECT_NAME)
        
    if new_settings.SENTRY_DSN is not None:
        settings.SENTRY_DSN = new_settings.SENTRY_DSN
        _update_setting(session, "SENTRY_DSN", str(new_settings.SENTRY_DSN))
        
    if new_settings.SMTP_HOST is not None:
        settings.SMTP_HOST = new_settings.SMTP_HOST
        _update_setting(session, "SMTP_HOST", new_settings.SMTP_HOST)
        
    if new_settings.SMTP_USER is not None:
        settings.SMTP_USER = new_settings.SMTP_USER
        _update_setting(session, "SMTP_USER", new_settings.SMTP_USER)
        
    if new_settings.SMTP_PASSWORD is not None:
        settings.SMTP_PASSWORD = new_settings.SMTP_PASSWORD
        _update_setting(session, "SMTP_PASSWORD", new_settings.SMTP_PASSWORD)
        
    if new_settings.EMAILS_FROM_EMAIL is not None:
        settings.EMAILS_FROM_EMAIL = new_settings.EMAILS_FROM_EMAIL
        _update_setting(session, "EMAILS_FROM_EMAIL", new_settings.EMAILS_FROM_EMAIL)
        
    if new_settings.EMAILS_FROM_NAME is not None:
        settings.EMAILS_FROM_NAME = new_settings.EMAILS_FROM_NAME
        _update_setting(session, "EMAILS_FROM_NAME", new_settings.EMAILS_FROM_NAME)
        
    if new_settings.SMTP_TLS is not None:
        settings.SMTP_TLS = new_settings.SMTP_TLS
        _update_setting(session, "SMTP_TLS", str(new_settings.SMTP_TLS))
        
    if new_settings.SMTP_SSL is not None:
        settings.SMTP_SSL = new_settings.SMTP_SSL
        _update_setting(session, "SMTP_SSL", str(new_settings.SMTP_SSL))
        
    if new_settings.SMTP_PORT is not None:
        settings.SMTP_PORT = new_settings.SMTP_PORT
        _update_setting(session, "SMTP_PORT", str(new_settings.SMTP_PORT))
    
    session.commit()
    return {"message": "Settings updated successfully"}
