import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, or_, select

from app.api.deps import CurrentUser, SessionDep
from app.crud import group as group_crud
from app.model.base import Message
from app.model.group import (
    Group,
    GroupCreate,
    GroupPublic,
    GroupsPublic,
    GroupUpdate,
)
from app.model.user import User

router = APIRouter(tags=["groups"], prefix="/groups")


@router.get("/", response_model=GroupsPublic)
def read_groups(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> GroupsPublic:
    """
    Retrieve groups.
    """
    # Get total count
    count_statement = select(func.count()).select_from(Group)
    # Get groups with pagination
    data_statement = (
        select(Group)
        .options(joinedload(Group.owner), joinedload(Group.members))
        .offset(skip)
        .limit(limit)
    )
    # Non-superusers can only see their own groups
    if not current_user.is_superuser:
        count_statement = count_statement.where(
            or_(
                Group.members.any(User.id == current_user.id),
                Group.owner_id == current_user.id,
            )
        )
        data_statement = data_statement.where(
            or_(
                Group.members.any(User.id == current_user.id),
                Group.owner_id == current_user.id,
            )
        )
    # Execute queries
    total = session.exec(count_statement).one()
    groups = session.exec(data_statement).unique().all()

    return GroupsPublic(groups=groups, total=total)


@router.get("/{group_id}", response_model=GroupPublic)
def read_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
) -> GroupPublic:
    """
    Get group by ID.
    """
    group = group_crud.get_group(session=session, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not current_user.is_superuser and current_user not in group.users:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return group


@router.post("/", response_model=GroupPublic)
def create_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_in: GroupCreate,
) -> GroupPublic:
    """
    Create new group.
    """
    # Ensure owner is added as a member if not already
    if current_user.id not in group_in.member_ids:
        group_in.member_ids.append(current_user.id)

    group = group_crud.create_group(
        session=session, group_create=group_in, owner_id=current_user.id
    )
    return group


@router.put("/{group_id}", response_model=GroupPublic)
def update_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
    group_in: GroupUpdate,
) -> GroupPublic:
    """
    Update a group.
    """
    group = group_crud.get_group(session=session, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not current_user.is_superuser and (group.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    group = group_crud.update_group(
        session=session, db_group=group, group_update=group_in
    )
    return group


@router.delete("/{group_id}", response_model=Message)
def delete_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
) -> Message:
    """
    Delete a group.
    """
    group = group_crud.get_group(session=session, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not current_user.is_superuser and (group.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    group_crud.delete_group(session=session, db_group=group)
    return Message(message="Group deleted successfully")
