import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.api.deps import SessionDep, get_current_active_superuser
from app.model.base import Message
from app.model.role import (
    Role,
    RoleCreate,
    RolePublic,
    RolesPublic,
    RoleUpdate,
)

router = APIRouter(tags=["Role"], prefix="/roles")


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolesPublic,
    summary="Retrieve roles",
)
def read_roles(session: SessionDep, skip: int = 0, limit: int = 1000) -> RolesPublic:
    """
    Retrieve roles.
    """
    total = session.exec(select(func.count()).select_from(Role)).one()
    roles = session.exec(select(Role).offset(skip).limit(limit)).all()
    return RolesPublic(roles=roles, total=total)


@router.get(
    "/{role_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolePublic,
    summary="Get role by ID",
)
def read_role(session: SessionDep, role_id: uuid.UUID) -> RolePublic:
    """
    Get role by ID.
    """
    # Fetch role
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolePublic,
    summary="Create new role",
)
def create_role(session: SessionDep, role_in: RoleCreate) -> Any:
    """
    Create new role.
    """
    # Create role
    role = Role.model_validate(role_in)

    # Save to database
    session.add(role)
    session.commit()
    session.refresh(role)

    return role


@router.put(
    "/{role_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RolePublic,
    summary="Update a role",
)
def update_role(session: SessionDep, role_id: uuid.UUID, role_in: RoleUpdate) -> Any:
    """
    Update a role.
    """
    # Fetch role
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Update fields
    data = role_in.model_dump(exclude_unset=True)
    role.sqlmodel_update(data)

    # Save to database
    session.add(role)
    session.commit()
    session.refresh(role)

    return role


@router.delete(
    "/{role_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    summary="Delete a role",
)
def delete_role(session: SessionDep, role_id: uuid.UUID) -> Any:
    """
    Delete a role.
    """
    # Fetch role
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Delete role
    session.delete(role)
    session.commit()

    return Message(detail="Role deleted successfully")
