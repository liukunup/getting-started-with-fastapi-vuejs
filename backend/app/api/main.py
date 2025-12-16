from fastapi import APIRouter

from app.api.routes import (
    apis,
    application,
    celery,
    group,
    item,
    login,
    menu,
    openapi,
    private,
    role,
    task,
    user,
    utils,
    policy,
)
from app.api.routes import (
    settings as settings_route,
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
api_router.include_router(menu.router)
api_router.include_router(role.router)
api_router.include_router(policy.router)

# The business logic routers
api_router.include_router(group.router)
api_router.include_router(item.router)
api_router.include_router(task.router)
api_router.include_router(apis.router)

# Include private routes only in local environment
if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
