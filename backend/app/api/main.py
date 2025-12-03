from fastapi import APIRouter

from app.api.routes import (
    application,
    celery,
    group,
    item,
    login,
    openapi,
    private,
    settings as settings_route,
    task,
    user,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(user.router)
api_router.include_router(login.router)
api_router.include_router(utils.router)
api_router.include_router(application.router)
api_router.include_router(openapi.router)
api_router.include_router(celery.router)
api_router.include_router(settings_route.router)

# The business logic routers
api_router.include_router(group.router)
api_router.include_router(item.router)
api_router.include_router(task.router)

# Include private routes only in local environment
if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
