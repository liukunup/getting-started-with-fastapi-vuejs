from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CacheDep, CurrentUser, SessionDep, get_current_active_superuser
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
)
from app.model.base import Message, NewPassword, Token
from app.model.user import UserPublic, UserRegister
from app.utils import (
    generate_reset_password_email,
    generate_reset_password_token,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["Login"])


@router.post("/login/access-token")
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
    return Token(
        access_token=create_access_token(user.id, expires_delta=access_token_expires)
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> UserPublic:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
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


@router.post("/reset-password/")
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
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
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


@router.post("/register", response_model=UserPublic)
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
