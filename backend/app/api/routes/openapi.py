import logging
from typing import Any

from fastapi import APIRouter

from app.model.base import Message

logger = logging.getLogger(__name__)


router = APIRouter(tags=["OpenAPI"], prefix="/openapi")


@router.get("/demo", response_model=Message, summary="OpenAPI demo endpoint")
def openapi_demo() -> Any:
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
    return Message(message="OpenAPI demo endpoint accessed successfully")
