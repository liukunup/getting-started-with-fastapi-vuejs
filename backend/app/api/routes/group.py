import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, or_, select

from app.api.deps import CurrentUser, SessionDep
from app.model.base import Message
from app.model.group import (
    Group,
    GroupCreate,
    GroupPublic,
    GroupsPublic,
    GroupUpdate,
)
from app.model.user import User

router = APIRouter(tags=["Group"], prefix="/groups")


@router.get("/", response_model=GroupsPublic)
def read_groups(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> GroupsPublic:
    """
    Retrieve groups.
    """
    # Build queries for count and data
    count_statement = select(func.count()).select_from(Group)
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

    # Execute queries and return results
    total = session.exec(count_statement).one()
    groups = session.exec(data_statement).unique().all()

    return GroupsPublic(groups=groups, total=total)


@router.get("/{group_id}", response_model=GroupPublic)
def read_group(
    session: SessionDep, current_user: CurrentUser, group_id: uuid.UUID
) -> GroupPublic:
    """
    Get group by ID.
    """
    # Fetch group
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not current_user.is_superuser and current_user not in group.users:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return group


@router.post("/", response_model=GroupPublic)
def create_group(
    *, session: SessionDep, current_user: CurrentUser, group_in: GroupCreate
) -> GroupPublic:
    """
    Create new group.
    """
    # Ensure owner is added as a member if not already
    if current_user.id not in group_in.member_ids:
        group_in.member_ids.append(current_user.id)

    # Create group
    group = Group.model_validate(group_in, update={"owner_id": current_user.id})
    if group_in.member_ids:
        members = session.exec(
            select(User).where(User.id.in_(group_in.member_ids))
        ).all()
        group.members = list(members)

    # Save to database
    session.add(group)
    session.commit()
    session.refresh(group)

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
    # Fetch group
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not current_user.is_superuser and (group.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Update fields
    data = group_in.model_dump(exclude_unset=True)
    # Handle member_ids separately
    if group_in.member_ids is not None:
        if group_in.member_ids:
            members = session.exec(
                select(User).where(User.id.in_(group_in.member_ids))
            ).all()
            group.members = list(members)
        else:
            group.members = []
        # Remove member_ids from group_data as it is not a field in Group model
        if "member_ids" in data:
            del data["member_ids"]
    # Update other fields
    group.sqlmodel_update(data)

    # Save to database
    session.add(group)
    session.commit()
    session.refresh(group)

    return group


@router.delete("/{group_id}", response_model=Message)
def delete_group(
    *, session: SessionDep, current_user: CurrentUser, group_id: uuid.UUID
) -> Message:
    """
    Delete a group.
    """
    # Fetch group
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not current_user.is_superuser and (group.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Delete group
    session.delete(group)
    session.commit()

    return Message(message="Group deleted successfully")
