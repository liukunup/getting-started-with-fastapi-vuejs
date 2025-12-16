import hashlib
import hmac
import time
import uuid

import jwt
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import cache
from app.core.casbin import enforcer
from app.core.config import settings
from app.core.database import engine
from app.core.security import ALGORITHM
from app.model.application import Application
from app.model.user import User


class CasbinMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Always allow OPTIONS for CORS
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract Authorization header
        authorization = request.headers.get("Authorization")

        user_id = None
        is_superuser = False
        subject = "api:guest"

        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")

                if user_id:
                    with Session(engine) as session:
                        statement = (
                            select(User)
                            .where(User.id == user_id)
                            .options(joinedload(User.role))
                        )
                        user = session.exec(statement).first()
                        if user:
                            is_superuser = user.is_superuser
                            # Determine subject
                            if user.role:
                                subject = f"api:{user.role.name}"

            except jwt.PyJWTError:
                pass

        # Superuser bypass
        if is_superuser:
            return await call_next(request)

        # Casbin enforcement
        if not enforcer.enforce(subject, request.url.path, request.method):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Not authorized"},
            )

        return await call_next(request)


class OpenApiMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only enforce on OpenAPI paths
        openapi_base_path = f"{settings.API_V1_STR}/openapi"
        if not request.url.path.startswith(openapi_base_path):
            return await call_next(request)

        # Extract headers
        x_app_id = request.headers.get("X-App-Id")
        x_timestamp = request.headers.get("X-Timestamp")
        x_sign = request.headers.get("X-Sign")
        x_trace_id = request.headers.get("X-Trace-Id")

        # 1. Prevent replay attacks
        if not x_trace_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing X-Trace-Id header"},
            )
        trace_key = f"openapi:trace:{x_trace_id}"
        if cache.redis.get(trace_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Replay attack detected"},
            )

        # 2. Check timestamp (e.g., 15 minutes expiration)
        if not x_timestamp:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing X-Timestamp header"},
            )
        try:
            timestamp_int = int(x_timestamp)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid timestamp format"},
            )
        # Check if timestamp is within allowed window (900 seconds)
        current_timestamp = int(time.time())
        if abs(current_timestamp - timestamp_int) > 900:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Timestamp expired"},
            )

        # 3. Validate App ID and retrieve App Key
        if not x_app_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing X-App-Id header"},
            )
        try:
            app_uuid = uuid.UUID(x_app_id)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid App ID format"},
            )
        # Retrieve application from database
        with Session(engine) as session:
            statement = select(Application).where(Application.app_id == app_uuid)
            app = session.exec(statement).first()
            if not app or not app.is_active:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid App ID or App is inactive"},
                )

            # 4. Verify Signature
            if not x_sign:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing X-Sign header"},
                )
            # Construct expected signature
            sign_str = (
                f"app_id={x_app_id}&timestamp={x_timestamp}&trace_id={x_trace_id}"
            )
            expected_sign = hmac.new(
                app.app_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_sign, x_sign):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid Signature"},
                )

        # Cache Trace ID with expiration (900s matches timestamp window)
        cache.redis.set(trace_key, "1", ex=900)

        return await call_next(request)
