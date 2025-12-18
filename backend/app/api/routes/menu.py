import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.casbin import enforcer
from app.model import Menu, MenuCreate, MenuTreeNode, MenuUpdate, Message

router = APIRouter(tags=["Menu"], prefix="/menus")


@router.get(
    "/",
    response_model=list[MenuTreeNode],
    summary="Retrieve menus",
)
def read_menus(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[MenuTreeNode]:
    """
    Retrieve menus.
    """
    # Fetch all menus
    menus = session.exec(select(Menu).order_by(Menu.sort)).all()

    # Convert to MenuTreeNode first to avoid modifying DB objects
    menu_map = {}
    for m in menus:
        mp = MenuTreeNode.model_validate(m)
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

    # Filter tree
    def filter_node(nodes: list[MenuTreeNode]) -> list[MenuTreeNode]:
        filtered = []
        for node in nodes:
            # Check permission
            is_accessible = False
            if current_user.is_superuser:
                is_accessible = True
            elif node.label:
                subject = (
                    f"menu:{current_user.role.name}" if current_user.role else None
                )
                is_accessible = enforcer.enforce(subject, node.label, "visible")

            # Decide whether to keep this node
            if is_accessible:
                # Recursively filter children
                if node.items:
                    node.items = filter_node(node.items)
                filtered.append(node)

        return filtered

    return filter_node(roots)


@router.get(
    "/{menu_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=MenuTreeNode,
    summary="Get menu by ID",
)
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


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=MenuTreeNode,
    summary="Create new menu",
)
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


@router.put(
    "/{menu_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=MenuTreeNode,
    summary="Update a menu",
)
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


@router.delete(
    "/{menu_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
    summary="Delete a menu",
)
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
