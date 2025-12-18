import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app import crud
from app.api.deps import (
    CacheDep,
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.casbin import enforcer
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.storage import storage
from app.model.base import Message
from app.model.menu import Menu, MenuTreeNode
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


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPrivate,
    summary="Retrieve users",
)
def read_users(session: SessionDep, offset: int = 0, limit: int = 100) -> UsersPrivate:
    """
    Retrieve users.
    """
    # Build queries for count and data
    count_statement = select(func.count()).select_from(User)
    data_statement = (
        select(User).options(joinedload(User.role)).offset(offset).limit(limit)
    )

    # Execute queries and return results
    total = session.exec(count_statement).one()
    users = session.exec(data_statement).all()

    return UsersPrivate(users=users, total=total)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPrivate,
    summary="Create new user",
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> UserPrivate:
    """
    Create new user.
    """
    # Check if user with the same email already exists
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )

    # Create user
    user = crud.create_user(session=session, user_create=user_in)
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


@router.patch("/me", response_model=UserPrivate, summary="Update own user")
def update_user_me(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_in: UserUpdateMe,
) -> UserPrivate:
    """
    Update own user.
    """
    # Check if email or username is changing to one that already exists
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    if user_in.username:
        existing_user = crud.get_user_by_username(
            session=session, username=user_in.username
        )
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this username already exists"
            )

    # Update user
    data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(data)

    # Save to database
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    # Ensure role is loaded
    if current_user.role_id and not current_user.role:
        session.refresh(current_user, ["role"])

    return current_user


@router.patch("/me/password", response_model=Message, summary="Update own password")
def update_password_me(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: UpdatePassword,
) -> Message:
    """
    Update own password.
    """
    # Verify old password
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    # Check new password is different
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )

    # Update password
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password

    # Save to database
    session.add(current_user)
    session.commit()

    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPrivate, summary="Get current user")
def read_user_me(current_user: CurrentUser) -> UserPrivate:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message, summary="Delete own user")
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Message:
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


@router.post("/signup", response_model=UserPublic, summary="Create new user")
def register_user(session: SessionDep, user_in: UserRegister) -> UserPublic:
    """
    Create new user without the need to be logged in.
    """
    # Check if user with the same email already exists
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )

    # Create user
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)

    return user


@router.get(
    "/{user_id}", response_model=UserPublic, summary="Get a specific user by id"
)
def read_user_by_id(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> UserPublic:
    """
    Get a specific user by id.
    """
    # Allow users to get their own info
    user = session.get(User, user_id)
    if user == current_user:
        return user
    # Only superusers can get other users' info
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
    summary="Update a user",
)
def update_user(
    *, session: SessionDep, user_id: uuid.UUID, user_in: UserUpdate
) -> UserPublic:
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
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    if user_in.username:
        existing_user = crud.get_user_by_username(
            session=session, username=user_in.username
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this username already exists"
            )

    # Update user
    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)

    return db_user


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    summary="Delete a user",
)
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
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
    summary="Force logout a user",
)
def force_logout(session: SessionDep, cache: CacheDep, user_id: uuid.UUID) -> Message:
    """
    Force logout a user.
    """
    # Check if user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Set timestamp in redis
    cache.redis.set(f"blacklist:user:{user_id}", datetime.now(timezone.utc).timestamp())

    return Message(message="User forced to logout")


@router.get(
    "/me/menu",
    response_model=list[MenuTreeNode],
    response_model_exclude_none=True,
    summary="Get current user menu",
)
def read_user_menu(
    session: SessionDep, current_user: CurrentUser
) -> list[MenuTreeNode]:
    """
    Get current user menu.
    """
    # 1. Fetch all menus
    menus = session.exec(select(Menu)).all()

    # 2. Build map
    menu_map = {}
    for m in menus:
        mp = MenuTreeNode.model_validate(m)
        menu_map[m.id] = mp

    # 3. Build tree
    roots = []
    for menu in menus:
        if menu.parent_id is None:
            roots.append(menu_map[menu.id])
        elif menu.parent_id in menu_map:
            parent = menu_map[menu.parent_id]
            if parent.items is None:
                parent.items = []
            parent.items.append(menu_map[menu.id])

    # 4. Filter tree
    def filter_node(nodes: list[MenuTreeNode]) -> list[MenuTreeNode]:
        filtered = []
        for node in nodes:
            # Check permission
            is_accessible = False
            if current_user.is_superuser:
                is_accessible = True
            elif node.name:
                subject = (
                    f"menu:{current_user.role.name}" if current_user.role else None
                )
                is_accessible = enforcer.enforce(subject, node.name, "visible")

            # Recursively filter children
            if node.items:
                node.items = filter_node(node.items)

            # Decide whether to keep this node
            if is_accessible:
                filtered.append(node)

        return filtered

    return filter_node(roots)


@router.post("/me/avatar", response_model=UserPublic, summary="Upload avatar")
def upload_avatar(
    session: SessionDep, current_user: CurrentUser, file: UploadFile = File(...)
) -> UserPublic:
    """
    Upload avatar.
    """
    # Validate content type
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Read file content
    content = file.file.read()

    # Save to storage
    object_name = storage.save_avatar(
        user_id=current_user.id,
        data=content,
        content_type=file.content_type,
    )

    # Update user
    current_user.avatar = object_name
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user
