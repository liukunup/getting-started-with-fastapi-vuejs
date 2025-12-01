from fastapi import APIRouter

from app.api.routes import (
    applications,
    groups,
    items,
    login,
    openapi,
    private,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(login.router)
api_router.include_router(utils.router)
api_router.include_router(applications.router)
api_router.include_router(openapi.router)

# The business logic routers
api_router.include_router(groups.router)
api_router.include_router(items.router)

# Include private routes only in local environment
if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
