import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.model.base import Message
from app.model.item import (
    Item,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)

router = APIRouter(tags=["Item"], prefix="/items")


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> ItemsPublic:
    """
    Retrieve items.
    """
    # Build queries for count and data
    count_statement = select(func.count()).select_from(Item)
    data_statement = (
        select(Item).options(joinedload(Item.owner)).offset(skip).limit(limit)
    )

    # Non-superusers can only see their own items
    if not current_user.is_superuser:
        count_statement = count_statement.where(Item.owner_id == current_user.id)
        data_statement = data_statement.where(Item.owner_id == current_user.id)

    # Execute queries and return results
    total = session.exec(count_statement).one()
    items = session.exec(data_statement).all()

    return ItemsPublic(items=items, total=total)


@router.get("/{item_id}", response_model=ItemPublic)
def read_item(
    session: SessionDep, current_user: CurrentUser, item_id: uuid.UUID
) -> ItemPublic:
    """
    Get item by ID.
    """
    # Fetch item
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> ItemPublic:
    """
    Create new item.
    """
    # Create item
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})

    # Save to database
    session.add(item)
    session.commit()
    session.refresh(item)

    return item


@router.put("/{item_id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
    item_in: ItemUpdate,
) -> ItemPublic:
    """
    Update an item.
    """
    # Fetch item
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Update fields
    data = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(data)

    # Save to database
    session.add(item)
    session.commit()
    session.refresh(item)

    return item


@router.delete("/{item_id}", response_model=Message)
def delete_item(
    session: SessionDep, current_user: CurrentUser, item_id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    # Fetch item
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Delete item
    session.delete(item)
    session.commit()

    return Message(message="Item deleted successfully")
