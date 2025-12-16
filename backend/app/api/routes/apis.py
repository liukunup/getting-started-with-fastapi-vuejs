from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.model.api import (
    Api,
    ApiCreate,
    ApiPublic,
    ApiUpdate,
    ApiTreeNode,
    ApisTreePublic,
)
from app.model.base import Message

router = APIRouter(tags=["API"], prefix="/apis")


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ApisTreePublic
)
def read_apis(
    session: SessionDep,
    skip: int = 0,
    limit: int = 1000,
) -> ApisTreePublic:
    """
    Retrieve apis.
    """
    # Fetch all apis
    total = session.exec(select(func.count()).select_from(Api)).one()
    apis = session.exec(
        select(Api).options(joinedload(Api.owner)).offset(skip).limit(limit)
    ).all()

    groups = {}
    for api in apis:
        if api.group not in groups:
            groups[api.group] = ApiTreeNode(
                key=f"group-{api.group}",
                data={
                    "name": api.group,
                    "isGroup": True
                },
                children=[]
            )
        
        api_data = ApiPublic.model_validate(api).model_dump(mode='json')
        api_data["isGroup"] = False
        
        groups[api.group].children.append(ApiTreeNode(
            key=str(api.id),
            data=api_data
        ))

    return ApisTreePublic(data=list(groups.values()), total=total)


@router.get(
    "/{api_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ApiPublic,
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
