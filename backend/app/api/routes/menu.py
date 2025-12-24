import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.casbin import enforcer
from app.model import Menu, MenuCreate, MenuTreeNode, MenuUpdate, Message, Role

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
    all_roles = session.exec(select(Role)).all()

    # Convert to MenuTreeNode first to avoid modifying DB objects
    menu_map = {}
    for m in menus:
        mp = MenuTreeNode.model_validate(m)
        mp.items = []

        # Populate roles
        allowed_roles = []
        for role in all_roles:
            subject = f"menu:{role.name}"
            # Check permission (label or name, with or without prefix)
            if (
                (mp.label and enforcer.enforce(subject, mp.label, "visible"))
                or (mp.name and enforcer.enforce(subject, mp.name, "visible"))
                or (mp.label and enforcer.enforce(role.name, mp.label, "visible"))
                or (mp.name and enforcer.enforce(role.name, mp.name, "visible"))
            ):
                allowed_roles.append(role.name)
        mp.roles = allowed_roles

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
            else:
                subject = (
                    f"menu:{current_user.role.name}" if current_user.role else None
                )
                # Check against label
                if node.label and enforcer.enforce(subject, node.label, "visible"):
                    is_accessible = True
                # Check against name (if available)
                elif node.name:
                    if enforcer.enforce(subject, node.name, "visible"):
                        is_accessible = True
                # Fallback: check without prefix (legacy)
                elif node.label and enforcer.enforce(
                    current_user.role.name, node.label, "visible"
                ):
                    is_accessible = True

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


@router.get(
    "/{menu_id}/policies",
    response_model=list[str],
    dependencies=[Depends(get_current_active_superuser)],
    summary="Get policies for a Menu",
)
def read_menu_policies(
    session: SessionDep,
    menu_id: uuid.UUID,
) -> Any:
    """
    Get policies (roles) for a specific Menu.
    """
    menu = session.get(Menu, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Ensure policies are up to date
    enforcer.load_policy()

    roles = session.exec(select(Role)).all()
    allowed_roles = []

    for role in roles:
        # Check permission for menu:{role.name}
        subject = f"menu:{role.name}"

        # Check against label (default for UI created menus)
        if enforcer.enforce(subject, menu.label, "visible"):
            allowed_roles.append(role.name)
            continue

        # Check against name (used in initial data)
        if menu.name and enforcer.enforce(subject, menu.name, "visible"):
            allowed_roles.append(role.name)
            continue

        # Also check without prefix just in case (legacy/fallback)
        if enforcer.enforce(role.name, menu.label, "visible"):
            allowed_roles.append(role.name)
            continue

        if menu.name and enforcer.enforce(role.name, menu.name, "visible"):
            allowed_roles.append(role.name)

    return allowed_roles
