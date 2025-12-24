import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.casbin import enforcer
from app.model import (
    Api,
    ApiCreate,
    ApiPublic,
    ApiTreeNode,
    ApiTreePublic,
    ApiUpdate,
    Message,
    Role,
)

router = APIRouter(tags=["API"], prefix="/apis")


@router.get(
    "/",
    response_model=ApiTreePublic,
    summary="Retrieve APIs",
)
def read_apis(
    session: SessionDep,
    current_user: CurrentUser,
) -> ApiTreePublic:
    """
    Retrieve apis.
    """
    # Fetch all apis
    total = session.exec(select(func.count()).select_from(Api)).one()
    apis = session.exec(select(Api).options(joinedload(Api.owner))).all()
    all_roles = session.exec(select(Role)).all()

    # Build tree structure grouped by 'group' attribute
    groups = {}
    for api in apis:
        # Check permission
        is_accessible = False
        if current_user.is_superuser:
            is_accessible = True
        else:
            subject = f"api:{current_user.role.name}" if current_user.role else None
            is_accessible = enforcer.enforce(subject, api.path, api.method)

        if not is_accessible:
            continue

        # Create group node if it doesn't exist
        if api.group not in groups:
            groups[api.group] = ApiTreeNode(
                key=f"group-{api.group}",
                data={"name": api.group, "isGroup": True},
                children=[],
            )

        # Calculate allowed roles for this API
        allowed_roles = []
        for role in all_roles:
            subject_api = f"api:{role.name}"
            if enforcer.enforce(subject_api, api.path, api.method):
                allowed_roles.append(role.name)
                continue

            # Also check without prefix just in case
            if enforcer.enforce(role.name, api.path, api.method):
                allowed_roles.append(role.name)

        api_data = ApiPublic.model_validate(api).model_dump(mode="json")
        api_data["isGroup"] = False
        api_data["roles"] = allowed_roles

        groups[api.group].children.append(ApiTreeNode(key=str(api.id), data=api_data))

    return ApiTreePublic(data=list(groups.values()), total=total)


@router.get(
    "/{api_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ApiPublic,
    summary="Get API by ID",
)
def read_api(
    session: SessionDep,
    api_id: uuid.UUID,
) -> ApiPublic:
    """
    Get api by ID.
    """
    # Fetch api
    api = session.get(Api, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="Api not found")

    return api


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ApiPublic,
    summary="Create new API",
)
def create_api(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    api_in: ApiCreate,
) -> ApiPublic:
    """
    Create new api.
    """
    # Create api
    api = Api.model_validate(api_in, update={"owner_id": current_user.id})

    # Save to database
    session.add(api)
    session.commit()
    session.refresh(api)

    return api


@router.put(
    "/{api_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ApiPublic,
    summary="Update an API",
)
def update_api(
    *,
    session: SessionDep,
    api_id: uuid.UUID,
    api_in: ApiUpdate,
) -> ApiPublic:
    """
    Update an api.
    """
    # Fetch api
    api = session.get(Api, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="Api not found")

    # Update fields
    data = api_in.model_dump(exclude_unset=True)
    api.sqlmodel_update(data)

    # Save to database
    session.add(api)
    session.commit()
    session.refresh(api)

    return api


@router.delete(
    "/{api_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    summary="Delete an API",
)
def delete_api(
    session: SessionDep,
    api_id: uuid.UUID,
) -> Message:
    """
    Delete an api.
    """
    # Fetch api
    api = session.get(Api, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="Api not found")

    # Delete api
    session.delete(api)
    session.commit()

    return Message(message="Api deleted successfully")


@router.get(
    "/{api_id}/policies",
    response_model=list[str],
    dependencies=[Depends(get_current_active_superuser)],
    summary="Get policies for an API",
)
def read_api_policies(
    session: SessionDep,
    api_id: uuid.UUID,
) -> Any:
    """
    Get policies (roles) for a specific API.
    """
    api = session.get(Api, api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")

    # Filter policies by checking permission for each role
    # This leverages Casbin's matching logic (including wildcards and keyMatch)
    roles = session.exec(select(Role)).all()
    allowed_roles = []

    for role in roles:
        # Check permission for api:{role.name}
        subject_api = f"api:{role.name}"
        if enforcer.enforce(subject_api, api.path, api.method):
            allowed_roles.append(role.name)
            continue

        # Also check without prefix just in case
        if enforcer.enforce(role.name, api.path, api.method):
            allowed_roles.append(role.name)

    return allowed_roles
