import uuid

from sqlmodel import Session, select

from app.model.item import Item, ItemCreate, ItemUpdate


def create_item(
    *, session: Session, item_create: ItemCreate, owner_id: uuid.UUID
) -> Item:
    db_obj = Item.model_validate(item_create, update={"owner_id": owner_id})
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_item(*, session: Session, item_id: uuid.UUID) -> Item | None:
    return session.get(Item, item_id)


def get_items_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Item]:
    statement = select(Item).where(Item.owner_id == owner_id).offset(skip).limit(limit)
    return session.exec(statement).all()


def update_item(*, session: Session, db_item: Item, item_update: ItemUpdate) -> Item:
    item_data = item_update.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def delete_item(*, session: Session, db_item: Item) -> None:
    session.delete(db_item)
    session.commit()
