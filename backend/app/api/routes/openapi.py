from fastapi import APIRouter

from app.api.deps import CurrentApp
from app.model.application import ApplicationPublic

router = APIRouter(tags=["openapi"], prefix="/openapi")


@router.get("/test", response_model=ApplicationPublic)
def openapi_test(
    current_app: CurrentApp,
) -> ApplicationPublic:
    """
    Test OpenAPI authentication.
    Requires headers:
    - X-App-Id: Application ID
    - X-Timestamp: Current timestamp
    - X-Sign: Signature
    - X-Trace-Id: Trace ID
    Signature generation:
    HMAC-SHA256(app_key, "app_id={app_id}&timestamp={timestamp}&trace_id={trace_id}")
    """
    return current_app
