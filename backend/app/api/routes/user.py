import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import (
    CacheDep,
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.storage import storage
from app.crud import user as user_crud
from app.model.base import Message
from app.model.user import (
    UpdatePassword,
    User,
    UserCreate,
    UserPrivate,
    UserPublic,
    UserRegister,
    UsersPrivate,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(tags=["User"], prefix="/users")


def convert_avatar_to_url(user: User) -> None:
    """Convert avatar path to full MinIO public URL for a user object."""
    if user.avatar and not user.avatar.startswith('http'):
        user.avatar = storage.get_file_url(user.avatar)


def convert_avatars_to_urls(users: list[User]) -> None:
    """Convert avatar paths to full URLs for a list of user objects."""
    for user in users:
        convert_avatar_to_url(user)


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPrivate,
)
def read_users(
    session: SessionDep,  # type: ignore
    offset: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve users.
    """
    # Get total count
    count_statement = select(func.count()).select_from(User)
    total = session.exec(count_statement).one()
    # Get users with pagination
    statement = select(User).options(joinedload(User.role)).offset(offset).limit(limit)
    users = session.exec(statement).all()
    # Convert avatar paths to URLs
    convert_avatars_to_urls(users)

    return UsersPrivate(users=users, total=total)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(
    *,
    user_in: UserCreate,
    session: SessionDep,  # type: ignore
) -> Any:
    """
    Create new user.
    """
    # Check if user with the same email already exists
    user = user_crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    # Create user
    user = user_crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.username, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPrivate)
def update_user_me(
    *,
    user_in: UserUpdateMe,
    session: SessionDep,  # type: ignore
    current_user: CurrentUser,  # type: ignore
) -> Any:
    """
    Update own user.
    """
    # Check if email or username is changing to one that already exists
    if user_in.email:
        existing_user = user_crud.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    if user_in.username:
        existing_user = user_crud.get_user_by_username(
            session=session, username=user_in.username
        )
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this username already exists"
            )
    # Update user
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    # Ensure role is loaded
    if current_user.role_id and not current_user.role:
        session.refresh(current_user, ["role"])
    # Convert avatar path to backend proxy URL
    convert_avatar_to_url(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *,
    body: UpdatePassword,
    session: SessionDep,  # type: ignore
    current_user: CurrentUser,  # type: ignore
) -> Any:
    """
    Update own password.
    """
    # Verify old password
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    # Check new password is different
    if body.old_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    # Update password
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPrivate)
def read_user_me(
    current_user: CurrentUser,  # type: ignore
) -> Any:
    """
    Get current user.
    """
    # Convert avatar path to backend proxy URL
    convert_avatar_to_url(current_user)
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(
    session: SessionDep,  # type: ignore
    current_user: CurrentUser,  # type: ignore
) -> Any:
    """
    Delete own user.
    """
    # Prevent superuser from deleting themselves
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    # Delete user
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(
    user_in: UserRegister,
    session: SessionDep,  # type: ignore
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    # Check if user with the same email already exists
    user = user_crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    # Create user
    user_create = UserCreate.model_validate(user_in)
    user = user_crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID,
    session: SessionDep,  # type: ignore
    current_user: CurrentUser,  # type: ignore
) -> Any:
    """
    Get a specific user by id.
    """
    # Allow users to get their own info
    user = session.get(User, user_id)
    if user == current_user:
        convert_avatar_to_url(user)
        return user
    # Only superusers can get other users' info
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    convert_avatar_to_url(user)
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    session: SessionDep,  # type: ignore
) -> Any:
    """
    Update a user.
    """
    # Check if user exists
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    # Check if email or username is changing to one that already exists
    if user_in.email:
        existing_user = user_crud.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    if user_in.username:
        existing_user = user_crud.get_user_by_username(
            session=session, username=user_in.username
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this username already exists"
            )
    # Update user
    db_user = user_crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    user_id: uuid.UUID,
    session: SessionDep,  # type: ignore
    current_user: CurrentUser,  # type: ignore
) -> Message:
    """
    Delete a user.
    """
    # Check if user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prevent superuser from deleting themselves
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    # Delete user
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post(
    "/{user_id}/force-logout",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def force_logout(
    user_id: uuid.UUID,
    session: SessionDep,
    cache: CacheDep,
) -> Any:
    """
    Force logout a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Set timestamp in redis
    cache.redis.set(f"blacklist:user:{user_id}", datetime.now(timezone.utc).timestamp())

    return Message(message="User forced to logout")


@router.post("/me/avatar", response_model=UserPrivate)
def upload_avatar(
    file: UploadFile = File(...),
    session: SessionDep = None,  # type: ignore
    current_user: CurrentUser = None,  # type: ignore
) -> Any:
    """
    Upload avatar for current user.
    """
    file_name = f"{current_user.id}/{file.filename}"
    object_path = storage.upload_file(file.file, file_name, file.content_type)

    # Store the object path in database
    current_user.avatar = object_path
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    # Ensure role is loaded
    if current_user.role_id and not current_user.role:
        session.refresh(current_user, ["role"])
    
    # Convert avatar path to backend proxy URL for response
    convert_avatar_to_url(current_user)
    
    return current_user


@router.get("/avatar/{user_id}")
def get_user_avatar(
    user_id: uuid.UUID,
    session: SessionDep,  # type: ignore
) -> Any:
    """
    Get user avatar image by user ID.
    This endpoint serves as a proxy to the MinIO storage.
    """
    user = session.get(User, user_id)
    if not user or not user.avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    try:
        # Get the file from MinIO
        response = storage.minio.get_object(settings.MINIO_BUCKET_NAME, user.avatar)
        
        # Determine content type
        content_type = "image/jpeg"
        if user.avatar.lower().endswith('.png'):
            content_type = "image/png"
        elif user.avatar.lower().endswith('.gif'):
            content_type = "image/gif"
        elif user.avatar.lower().endswith('.webp'):
            content_type = "image/webp"
        
        # Return the image as a streaming response
        return StreamingResponse(
            BytesIO(response.read()),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=604800",  # Cache for 7 days
                "Content-Disposition": f"inline; filename=avatar.jpg"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to retrieve avatar: {str(e)}")
