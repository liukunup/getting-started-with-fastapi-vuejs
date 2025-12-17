import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.model import (
    Application,
    ApplicationCreate,
    ApplicationPrivate,
    ApplicationPublic,
    ApplicationsPublic,
    ApplicationUpdate,
    Message,
)

router = APIRouter(tags=["Application"], prefix="/apps")


@router.get("/", response_model=ApplicationsPublic, summary="Retrieve applications")
def read_applications(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> ApplicationsPublic:
    """
    Retrieve applications.
    """
    # Build queries for count and data
    count_statement = select(func.count()).select_from(Application)
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

    # Execute queries and return results
    total = session.exec(count_statement).one()
    apps = session.exec(data_statement).all()

    return ApplicationsPublic(applications=apps, total=total)


@router.get("/{app_id}", response_model=ApplicationPublic, summary="Get application by ID")
def read_application(
    session: SessionDep, current_user: CurrentUser, app_id: uuid.UUID
) -> ApplicationPublic:
    """
    Get application by ID.
    """
    # Fetch application
    app = session.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not current_user.is_superuser and (app.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return app


@router.post("/", response_model=ApplicationPrivate, summary="Create new application")
def create_application(
    *, session: SessionDep, current_user: CurrentUser, app_in: ApplicationCreate
) -> ApplicationPrivate:
    """
    Create new application.
    """
    # Create application
    app = Application.model_validate(
        app_in,
        update={
            "owner_id": current_user.id,
        },
    )

    # Save to database
    session.add(app)
    session.commit()
    session.refresh(app)

    return app


@router.put("/{app_id}", response_model=ApplicationPublic, summary="Update an application")
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
    # Fetch application
    app = session.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not current_user.is_superuser and (app.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Update fields
    data = app_in.model_dump(exclude_unset=True)
    app.sqlmodel_update(data)

    # Save to database
    session.add(app)
    session.commit()
    session.refresh(app)

    return app


@router.delete("/{app_id}", response_model=Message, summary="Delete an application")
def delete_application(
    *, session: SessionDep, current_user: CurrentUser, app_id: uuid.UUID
) -> Message:
    """
    Delete an application.
    """
    # Fetch application
    app = session.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not current_user.is_superuser and (app.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Delete from database
    session.delete(app)
    session.commit()

    return Message(message="Application deleted successfully")
