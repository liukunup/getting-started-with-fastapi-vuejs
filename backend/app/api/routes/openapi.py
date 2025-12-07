import logging

from fastapi import APIRouter

from app.api.deps import CurrentApp
from app.model.application import ApplicationPublic

logger = logging.getLogger(__name__)


router = APIRouter(tags=["OpenAPI"], prefix="/openapi")


@router.get("/demo", response_model=ApplicationPublic)
def openapi_demo(current_app: CurrentApp) -> ApplicationPublic:
    """
    OpenAPI demo endpoint.

    Requires headers:
    - X-App-Id: Application ID
    - X-Timestamp: Current timestamp
    - X-Sign: Signature
    - X-Trace-Id: Trace ID

    Signature generation:
    HMAC-SHA256(app_key, "app_id={app_id}&timestamp={timestamp}&trace_id={trace_id}")
    """
    logger.info("OpenAPI demo endpoint accessed")
    return current_app
