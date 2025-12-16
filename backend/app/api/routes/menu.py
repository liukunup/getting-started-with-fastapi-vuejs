import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.model.base import Message
from app.model.menu import Menu, MenuCreate, MenuPublic, MenuUpdate

router = APIRouter(tags=["Menu"], prefix="/menus")


@router.get("/",     dependencies=[Depends(get_current_active_superuser)], response_model=list[MenuPublic])
def read_menus(
    session: SessionDep,
) -> list[MenuPublic]:
    """
    Retrieve menus.
    """
    # Fetch all menus
    menus = session.exec(select(Menu)).all()

    # Convert to MenuPublic first to avoid modifying DB objects
    menu_map = {}
    for m in menus:
        mp = MenuPublic.model_validate(m)
        mp.items = []
        menu_map[m.id] = mp

    # Build tree structure
    roots = []
    for menu in menus:
        if menu.parent_id is None:
            roots.append(menu_map[menu.id])
        elif menu.parent_id in menu_map:
            parent = menu_map[menu.parent_id]
            parent.items.append(menu_map[menu.id])

    print(f"Returning {len(roots)} root menus")
    return roots


@router.get("/{menu_id}",    dependencies=[Depends(get_current_active_superuser)], response_model=MenuPublic)
def read_menu(
    session: SessionDep,
    menu_id: uuid.UUID,
) -> Any:
    """
    Get menu by ID.
    """
    # Fetch menu
    menu = session.get(Menu, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    return menu


@router.post("/",     dependencies=[Depends(get_current_active_superuser)], response_model=MenuPublic)
def create_menu(
    *,
    session: SessionDep,
    menu_in: MenuCreate,
) -> Any:
    """
    Create new menu.
    """
    # Create menu
    menu = Menu.model_validate(menu_in)

    # Save to database
    session.add(menu)
    session.commit()
    session.refresh(menu)

    return menu


@router.put("/{menu_id}",     dependencies=[Depends(get_current_active_superuser)], response_model=MenuPublic)
def update_menu(
    *,
    session: SessionDep,
    menu_id: uuid.UUID,
    menu_in: MenuUpdate,
) -> Any:
    """
    Update a menu.
    """
    # Fetch menu
    menu = session.get(Menu, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Update fields
    data = menu_in.model_dump(exclude_unset=True)
    menu.sqlmodel_update(data)

    # Save to database
    session.add(menu)
    session.commit()
    session.refresh(menu)

    return menu


@router.delete("/{menu_id}",     dependencies=[Depends(get_current_active_superuser)], response_model=Message)
def delete_menu(
    *,
    session: SessionDep,
    menu_id: uuid.UUID,
) -> Message:
    """
    Delete a menu.
    """
    # Fetch menu
    menu = session.get(Menu, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Delete menu
    session.delete(menu)
    session.commit()

    return Message(message="Menu deleted successfully")
