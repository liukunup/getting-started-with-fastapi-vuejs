import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.crud import item as item_crud
from app.model.base import Message
from app.model.item import (
    Item,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)

router = APIRouter(tags=["items"], prefix="/items")


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> ItemsPublic:
    """
    Retrieve items.
    """
    # Get total count
    count_statement = select(func.count()).select_from(Item)
    # Get items with pagination
    data_statement = (
        select(Item).options(joinedload(Item.owner)).offset(skip).limit(limit)
    )
    # Non-superusers can only see their own items
    if not current_user.is_superuser:
        count_statement = count_statement.where(Item.owner_id == current_user.id)
        data_statement = data_statement.where(Item.owner_id == current_user.id)
    # Execute queries
    total = session.exec(count_statement).one()
    items = session.exec(data_statement).all()

    return ItemsPublic(items=items, total=total)


@router.get("/{item_id}", response_model=ItemPublic)
def read_item(
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> ItemPublic:
    """
    Get item by ID.
    """
    item = item_crud.get_item(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_in: ItemCreate,
) -> ItemPublic:
    """
    Create new item.
    """
    item = item_crud.create_item(
        session=session, item_create=item_in, owner_id=current_user.id
    )
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
    item = item_crud.get_item(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    item = item_crud.update_item(session=session, db_item=item, item_update=item_in)
    return item


@router.delete("/{item_id}", response_model=Message)
def delete_item(
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> Message:
    """
    Delete an item.
    """
    item = item_crud.get_item(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    item_crud.delete_item(session=session, db_item=item)
    return Message(message="Item deleted successfully")
