import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from app import crud
from app.api.deps import CacheDep, CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.model.base import Message, NewPassword, Token, TokenPayload
from app.model.user import User, UserCreate, UserPublic, UserRegister
from app.utils import (
    generate_reset_password_email,
    generate_reset_password_token,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["Login"])


@router.get("/login/config", summary="Get login configuration")
def get_login_config():
    """
    Get login configuration
    """
    return {
        "oidc_enabled": settings.OIDC_ENABLED,
        "oidc_name": settings.OIDC_NAME,
        "oidc_auto_login": settings.AUTO_LOGIN,
    }


@router.post(
    "/login/access-token", response_model=Token, summary="OAuth2 access token login"
)
def login_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return Token(
        access_token=create_access_token(user.id, expires_delta=access_token_expires),
        refresh_token=create_refresh_token(
            user.id, expires_delta=refresh_token_expires
        ),
    )


@router.post(
    "/login/refresh-token", response_model=Token, summary="Refresh access token"
)
def refresh_token(session: SessionDep, refresh_token: str) -> Token:
    """
    Refresh access token
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )

    if token_data.type != "refresh":
        raise HTTPException(
            status_code=403,
            detail="Invalid token type",
        )

    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return Token(
        access_token=create_access_token(user.id, expires_delta=access_token_expires),
        refresh_token=create_refresh_token(
            user.id, expires_delta=refresh_token_expires
        ),
    )


@router.post(
    "/login/test-token", response_model=UserPublic, summary="Test access token"
)
def test_token(current_user: CurrentUser) -> UserPublic:
    """
    Test access token
    """
    return current_user


@router.post("/login/password-recovery/{email}", summary="Password Recovery")
def recover_password(session: SessionDep, cache: CacheDep, email: str) -> Message:
    """
    Password Recovery
    """
    # Rate limit
    key = f"pwd:recovery:{email}:{datetime.now(timezone.utc).date()}"
    count = cache.redis.incr(key)
    if count == 1:
        cache.redis.expire(key, 86400)
    if count > 3:
        raise HTTPException(
            status_code=400, detail="Max password recovery attempts reached for today"
        )

    # Send email
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system",
        )
    password_reset_token = generate_reset_password_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, username=user.username, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )

    return Message(message="Password recovery email sent")


@router.post("/login/reset-password/", summary="Reset password")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    # Verify token
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")

    # Update password
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password

    # Save to database
    session.add(user)
    session.commit()

    return Message(message="Password updated successfully")


@router.post(
    "/login/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
    summary="HTML Content for Password Recovery",
)
def recover_password_html_content(session: SessionDep, email: str) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system",
        )
    password_reset_token = generate_reset_password_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, username=user.username, token=password_reset_token
    )
    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )


@router.post("/register", response_model=UserPublic, summary="Register a new user")
def register(session: SessionDep, user_in: UserRegister) -> UserPublic:
    """
    Register a new user
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserRegister.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/login/oidc", summary="OIDC login")
def login_oidc(request: Request):  # noqa: ARG001
    """
    Redirect to OpenID Connect provider for login
    """
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=403, detail="OIDC is not enabled")

    if not settings.oidc_configured:
        raise HTTPException(status_code=501, detail="OIDC is not configured")

    redirect_uri = f"{settings.FRONTEND_HOST}{settings.API_V1_STR}/login/oidc/callback"

    return RedirectResponse(
        f"{settings.OIDC_AUTH_URL}?"
        f"client_id={settings.OIDC_CLIENT_ID}&"
        f"response_type=code&"
        f"scope={settings.OIDC_SCOPES}&"
        f"redirect_uri={redirect_uri}"
    )


@router.get("/login/oidc/callback", summary="OIDC login callback")
async def login_oidc_callback(session: SessionDep, request: Request, code: str):  # noqa: ARG001
    """
    Callback for OpenID Connect login
    """
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=403, detail="OIDC is not enabled")

    if not settings.oidc_configured:
        raise HTTPException(status_code=501, detail="OIDC is not configured")

    redirect_uri = f"{settings.FRONTEND_HOST}{settings.API_V1_STR}/login/oidc/callback"

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            settings.OIDC_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.OIDC_CLIENT_ID,
                "client_secret": settings.OIDC_CLIENT_SECRET,
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="OIDC login failed")

        token_data = response.json()
        id_token = token_data.get("id_token")

        # Decode ID Token without verification for simplicity in this example
        payload = jwt.decode(id_token, options={"verify_signature": False})

        sub = payload.get("sub")
        email = payload.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in OIDC token")

        # Find user by OIDC sub
        user = crud.get_user_by_oidc_sub(session=session, oidc_sub=sub)
        if not user:
            # Find user by email
            user = crud.get_user_by_email(session=session, email=email)
            if not user:
                # Create new user
                user_in = UserCreate(
                    email=email,
                    username=payload.get("preferred_username"),
                    password=secrets.token_urlsafe(32),  # Use random password
                    full_name=payload.get("name"),
                )
                user = crud.create_user(session=session, user_create=user_in)

            # Link OIDC sub to user
            user.oidc_sub = sub
            session.add(user)
            session.commit()
            session.refresh(user)

        # Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(user.id, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(
            user.id, expires_delta=refresh_token_expires
        )

        # Redirect to frontend with token
        return RedirectResponse(
            f"{settings.FRONTEND_HOST}/auth/login?access_token={access_token}&refresh_token={refresh_token}"
        )


@router.get("/logout/oidc", summary="Logout and redirect to OIDC provider")
def logout_oidc(request: Request):  # noqa: ARG001
    """
    Redirect to OpenID Connect provider for logout
    """
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=403, detail="OIDC is not enabled")

    if not settings.oidc_configured:
        raise HTTPException(status_code=501, detail="OIDC is not configured")

    if not settings.SIGNOUT_REDIRECT_URL:
        raise HTTPException(
            status_code=501, detail="The signout redirect url is not configured"
        )

    post_logout_redirect_uri = f"{settings.FRONTEND_HOST}/login"

    return RedirectResponse(
        f"{settings.SIGNOUT_REDIRECT_URL}?"
        f"post_logout_redirect_uri={post_logout_redirect_uri}&"
        f"client_id={settings.OIDC_CLIENT_ID}"
    )
