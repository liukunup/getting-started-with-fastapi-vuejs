import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.crud import application as app_crud
from app.model.application import (
    Application,
    ApplicationCreate,
    ApplicationPrivate,
    ApplicationPublic,
    ApplicationsPublic,
    ApplicationUpdate,
)
from app.model.base import Message

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/", response_model=ApplicationsPublic)
def read_applications(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> ApplicationsPublic:
    """
    Retrieve applications.
    """
    # Get total count
    count_statement = select(func.count()).select_from(Application)
    # Get items with pagination
    data_statement = (
        select(Application)
        .options(joinedload(Application.owner))
        .offset(skip)
        .limit(limit)
    )
    # Non-superusers can only see their own items
    if not current_user.is_superuser:
        count_statement = count_statement.where(Application.owner_id == current_user.id)
        data_statement = data_statement.where(Application.owner_id == current_user.id)
    # Execute queries
    total = session.exec(count_statement).one()
    applications = session.exec(data_statement).all()

    return ApplicationsPublic(applications=applications, total=total)


@router.get("/{app_id}", response_model=ApplicationPublic)
def read_application(
    session: SessionDep,
    current_user: CurrentUser,
    app_id: uuid.UUID,
) -> ApplicationPublic:
    """
    Get application by ID.
    """
    app = app_crud.get_application(session=session, application_id=app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not current_user.is_superuser and (app.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return app


@router.post("/", response_model=ApplicationPrivate)
def create_application(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    app_in: ApplicationCreate,
) -> ApplicationPrivate:
    """
    Create new application.
    """
    application = app_crud.create_application(
        session=session, application_create=app_in, owner_id=current_user.id
    )
    return application


@router.put("/{app_id}", response_model=ApplicationPublic)
def update_application(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    app_id: uuid.UUID,
    app_in: ApplicationUpdate,
) -> ApplicationPublic:
    """
    Update an application.
    """
    app = app_crud.get_application(session=session, application_id=app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not current_user.is_superuser and (app.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    app = app_crud.update_application(
        session=session, db_application=app, application_update=app_in
    )
    return app


@router.delete("/{app_id}", response_model=ApplicationPublic)
def delete_application(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    app_id: uuid.UUID,
) -> Message:
    """
    Delete an application.
    """
    app = app_crud.get_application(session=session, application_id=app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not current_user.is_superuser and (app.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    app_crud.delete_application(session=session, db_application=app)
    return Message(message="Application deleted successfully")
