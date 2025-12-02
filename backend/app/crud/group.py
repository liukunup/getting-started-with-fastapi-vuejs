import uuid

from sqlmodel import Session, select

from app.model.group import Group, GroupCreate, GroupUpdate
from app.model.user import User


def create_group(
    *, session: Session, group_create: GroupCreate, owner_id: uuid.UUID
) -> Group:
    db_obj = Group.model_validate(group_create, update={"owner_id": owner_id})
    if group_create.member_ids:
        members = session.exec(
            select(User).where(User.id.in_(group_create.member_ids))
        ).all()
        db_obj.members = list(members)

    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_group(*, session: Session, group_id: uuid.UUID) -> Group | None:
    return session.get(Group, group_id)


def get_groups_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Group]:
    statement = (
        select(Group).where(Group.owner_id == owner_id).offset(skip).limit(limit)
    )
    return session.exec(statement).all()


def update_group(
    *, session: Session, db_group: Group, group_update: GroupUpdate
) -> Group:
    group_data = group_update.model_dump(exclude_unset=True)

    if group_update.member_ids is not None:
        if group_update.member_ids:
            members = session.exec(
                select(User).where(User.id.in_(group_update.member_ids))
            ).all()
            db_group.members = list(members)
        else:
            db_group.members = []
        # Remove member_ids from group_data as it is not a field in Group model
        if "member_ids" in group_data:
            del group_data["member_ids"]

    db_group.sqlmodel_update(group_data)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group


def delete_group(*, session: Session, db_group: Group) -> None:
    session.delete(db_group)
    session.commit()
