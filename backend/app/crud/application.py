import uuid

from sqlmodel import Session, select

from app.model.application import Application, ApplicationCreate, ApplicationUpdate


def create_application(
    *, session: Session, application_create: ApplicationCreate, owner_id: uuid.UUID
) -> Application:
    db_obj = Application.model_validate(
        application_create,
        update={
            "owner_id": owner_id,
        },
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_application(
    *, session: Session, application_id: uuid.UUID
) -> Application | None:
    return session.get(Application, application_id)


def get_application_by_appid(*, session: Session, app_id: str) -> Application | None:
    statement = select(Application).where(Application.app_id == app_id)
    return session.exec(statement).first()


def get_applications_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Application]:
    statement = (
        select(Application)
        .where(Application.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def update_application(
    *,
    session: Session,
    db_application: Application,
    application_update: ApplicationUpdate,
) -> Application:
    application_data = application_update.model_dump(exclude_unset=True)
    db_application.sqlmodel_update(application_data)
    session.add(db_application)
    session.commit()
    session.refresh(db_application)
    return db_application


def delete_application(*, session: Session, db_application: Application) -> None:
    session.delete(db_application)
    session.commit()
