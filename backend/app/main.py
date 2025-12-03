import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.api.main import api_router
from app.core.config import settings
from app.core.database import engine
from app.model.system_setting import SystemSetting


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


# Load settings from DB
try:
    with Session(engine) as session:
        db_settings = session.exec(select(SystemSetting)).all()
        for setting in db_settings:
            if hasattr(settings, setting.key):
                val = setting.value
                if setting.key == "SMTP_PORT":
                    val = int(val)
                elif setting.key in ["SMTP_TLS", "SMTP_SSL"]:
                    val = val == "True"
                setattr(settings, setting.key, val)
except Exception as e:
    print(f"Warning: Could not load settings from DB: {e}")


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
