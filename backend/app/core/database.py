from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.model.application import Application, ApplicationCreate
from app.model.group import Group, GroupCreate
from app.model.item import Item, ItemCreate
from app.model.menu import Menu, MenuCreate
from app.model.user import Role, User, UserCreate

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    connect_args={"check_same_thread": False}
    if settings.DATABASE_TYPE == "sqlite"
    else {},
)

# make sure all SQLModel models are imported (app.model) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    # 1. Create initial superuser
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    # 2. Create initial roles
    for role_name in ["admin", "user", "guest"]:
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        if not role:
            role = Role(name=role_name, description=role_name.capitalize())
            session.add(role)
            session.commit()

    # 3. Create initial casbin policies for api access control
    from app.core.casbin import enforcer

    # Dev policies
    enforcer.add_policy("api:guest", "/docs", "GET")
    enforcer.add_policy("api:guest", "/redoc", "GET")
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/utils/healthz/", "GET")
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/openapi.json", "GET")
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/openapi/*", "GET")

    # Guest policies
    enforcer.add_policy(
        "api:guest", f"{settings.API_V1_STR}/login/access-token", "POST"
    )
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/login/test-token", "POST")
    enforcer.add_policy(
        "api:guest", f"{settings.API_V1_STR}/password-recovery/*", "POST"
    )
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/reset-password/", "POST")
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/register", "POST")
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/login/oidc", "GET")
    enforcer.add_policy(
        "api:guest", f"{settings.API_V1_STR}/login/oidc/callback", "GET"
    )

    # User policies (inherit from guest if needed, or define specific)
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/utils/healthz/", "GET")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/openapi.json", "GET")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/openapi/*", "GET")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/users/*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/menus/*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/items/*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/groups/*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/apps/*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/tasks/*", "*")

    # Admin policies
    # Usually admin has all permissions, handled by is_superuser check or wildcard policy
    enforcer.add_policy("api:admin", "/*", "*")

    # 4. Create initial menus
    menus = [
        {
            "label": "Home",
            "items": [
                {"label": "Dashboard", "icon": "pi pi-fw pi-home", "to": "/"},
                {"label": "Items", "icon": "pi pi-fw pi-list", "to": "/items"},
                {"label": "Groups", "icon": "pi pi-fw pi-users", "to": "/groups"},
                {
                    "label": "Applications",
                    "icon": "pi pi-fw pi-box",
                    "to": "/applications",
                },
                {"label": "Tasks", "icon": "pi pi-fw pi-clock", "to": "/tasks"},
                {
                    "label": "Task Executions",
                    "icon": "pi pi-fw pi-history",
                    "to": "/task-executions",
                },
                {"label": "Profile", "icon": "pi pi-fw pi-user", "to": "/profile"},
            ],
        },
        {
            "label": "Admin",
            "items": [
                {"label": "Celery", "icon": "pi pi-fw pi-chart-line", "to": "/celery"},
                {"label": "Menus", "icon": "pi pi-fw pi-bars", "to": "/admin/menus"},
                {"label": "APIs", "icon": "pi pi-fw pi-sitemap", "to": "/admin/apis"},
                {"label": "Roles", "icon": "pi pi-fw pi-id-card", "to": "/admin/roles"},
                {"label": "Users", "icon": "pi pi-fw pi-user", "to": "/users"},
                {"label": "Settings", "icon": "pi pi-fw pi-cog", "to": "/settings"},
            ],
        },
        {
            "label": "UI Components",
            "items": [
                {
                    "label": "Form Layout",
                    "icon": "pi pi-fw pi-id-card",
                    "to": "/uikit/formlayout",
                },
                {
                    "label": "Input",
                    "icon": "pi pi-fw pi-check-square",
                    "to": "/uikit/input",
                },
                {
                    "label": "Button",
                    "icon": "pi pi-fw pi-mobile",
                    "to": "/uikit/button",
                    "clazz": "rotated-icon",
                },
                {"label": "Table", "icon": "pi pi-fw pi-table", "to": "/uikit/table"},
                {"label": "List", "icon": "pi pi-fw pi-list", "to": "/uikit/list"},
                {"label": "Tree", "icon": "pi pi-fw pi-share-alt", "to": "/uikit/tree"},
                {"label": "Panel", "icon": "pi pi-fw pi-tablet", "to": "/uikit/panel"},
                {
                    "label": "Overlay",
                    "icon": "pi pi-fw pi-clone",
                    "to": "/uikit/overlay",
                },
                {"label": "Media", "icon": "pi pi-fw pi-image", "to": "/uikit/media"},
                {"label": "Menu", "icon": "pi pi-fw pi-bars", "to": "/uikit/menu"},
                {
                    "label": "Message",
                    "icon": "pi pi-fw pi-comment",
                    "to": "/uikit/message",
                },
                {"label": "File", "icon": "pi pi-fw pi-file", "to": "/uikit/file"},
                {
                    "label": "Chart",
                    "icon": "pi pi-fw pi-chart-bar",
                    "to": "/uikit/charts",
                },
                {
                    "label": "Timeline",
                    "icon": "pi pi-fw pi-calendar",
                    "to": "/uikit/timeline",
                },
                {"label": "Misc", "icon": "pi pi-fw pi-circle", "to": "/uikit/misc"},
            ],
        },
        {
            "label": "Prime Blocks",
            "icon": "pi pi-fw pi-prime",
            "items": [
                {"label": "Free Blocks", "icon": "pi pi-fw pi-eye", "to": "/blocks"},
                {
                    "label": "All Blocks",
                    "icon": "pi pi-fw pi-globe",
                    "url": "https://blocks.primevue.org/",
                    "target": "_blank",
                },
            ],
        },
        {
            "label": "Pages",
            "icon": "pi pi-fw pi-briefcase",
            "to": "/pages",
            "items": [
                {"label": "Landing", "icon": "pi pi-fw pi-globe", "to": "/landing"},
                {
                    "label": "Auth",
                    "icon": "pi pi-fw pi-user",
                    "items": [
                        {
                            "label": "Login",
                            "icon": "pi pi-fw pi-sign-in",
                            "to": "/auth/login",
                        },
                        {
                            "label": "Error",
                            "icon": "pi pi-fw pi-times-circle",
                            "to": "/auth/error",
                        },
                        {
                            "label": "Access Denied",
                            "icon": "pi pi-fw pi-lock",
                            "to": "/auth/access",
                        },
                    ],
                },
                {"label": "Crud", "icon": "pi pi-fw pi-pencil", "to": "/pages/crud"},
                {
                    "label": "Not Found",
                    "icon": "pi pi-fw pi-exclamation-circle",
                    "to": "/pages/notfound",
                },
                {
                    "label": "Empty",
                    "icon": "pi pi-fw pi-circle-off",
                    "to": "/pages/empty",
                },
            ],
        },
        {
            "label": "Hierarchy",
            "items": [
                {
                    "label": "Submenu 1",
                    "icon": "pi pi-fw pi-bookmark",
                    "items": [
                        {
                            "label": "Submenu 1.1",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 1.1.1",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                                {
                                    "label": "Submenu 1.1.2",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                                {
                                    "label": "Submenu 1.1.3",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                            ],
                        },
                        {
                            "label": "Submenu 1.2",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 1.2.1",
                                    "icon": "pi pi-fw pi-bookmark",
                                }
                            ],
                        },
                    ],
                },
                {
                    "label": "Submenu 2",
                    "icon": "pi pi-fw pi-bookmark",
                    "items": [
                        {
                            "label": "Submenu 2.1",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 2.1.1",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                                {
                                    "label": "Submenu 2.1.2",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                            ],
                        },
                        {
                            "label": "Submenu 2.2",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 2.2.1",
                                    "icon": "pi pi-fw pi-bookmark",
                                }
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "label": "Get Started",
            "items": [
                {
                    "label": "Documentation",
                    "icon": "pi pi-fw pi-book",
                    "to": "/documentation",
                },
                {
                    "label": "View Source",
                    "icon": "pi pi-fw pi-github",
                    "url": "https://github.com/primefaces/sakai-vue",
                    "target": "_blank",
                },
            ],
        },
    ]

    def create_menu(session: Session, menu_create: MenuCreate, owner_id=None) -> Menu:
        """Create a menu item in the database."""
        menu = Menu.model_validate(menu_create, update={"owner_id": owner_id})
        session.add(menu)
        session.commit()
        session.refresh(menu)
        return menu

    def create_menu_recursive(menu_data, parent_id=None, owner_id=None):
        """Recursively create menu items."""
        # Get label
        label = menu_data["label"]
        # Query existing menu
        query = select(Menu).where(Menu.label == label)
        if parent_id:
            query = query.where(Menu.parent_id == parent_id)
        else:
            query = query.where(Menu.parent_id == None)
        existing_menu = session.exec(query).first()

        if not existing_menu:
            menu_in = MenuCreate(
                label=label,
                icon=menu_data.get("icon"),
                to=menu_data.get("to"),
                url=menu_data.get("url"),
                target=menu_data.get("target"),
                component=menu_data.get("component"),
                clazz=menu_data.get("clazz"),
                parent_id=parent_id,
            )
            existing_menu = create_menu(
                session=session, menu_create=menu_in, owner_id=owner_id
            )

        if "items" in menu_data:
            for item in menu_data["items"]:
                create_menu_recursive(item, parent_id=existing_menu.id)

    for menu in menus:
        create_menu_recursive(menu)

    # 5. Create initial casbin policies for menu
    # Configure menu visibility based on roles

    # Common menus accessible by user and admin
    common_menus = [
        "Home",
        "UI Components",
        "Prime Blocks",
        "Pages",
        "Hierarchy",
        "Get Started",
    ]
    for menu_label in common_menus:
        enforcer.add_policy("menu:user", menu_label, "visible")
        enforcer.add_policy("menu:admin", menu_label, "visible")

    # Admin only menus
    admin_menus = ["Admin"]
    for menu_label in admin_menus:
        enforcer.add_policy("menu:admin", menu_label, "visible")

    # 6. Create initial data for dev & testing
    if settings.ENVIRONMENT == "local":
        for i in range(1, 52):
            # Create users
            email = f"user{i}@example.com"
            user = session.exec(select(User).where(User.email == email)).first()
            if not user:
                user_in = UserCreate(
                    email=email,
                    password="changethis",
                    full_name=f"User {i}",
                    is_superuser=False,
                )
                user = crud.create_user(session=session, user_create=user_in)

            # Create items
            item_name = f"Item {i}"
            item = session.exec(select(Item).where(Item.name == item_name)).first()
            if not item:
                item_in = ItemCreate(
                    name=item_name,
                    description=f"This is item {i}",
                )
                item = Item.model_validate(item_in, update={"owner_id": user.id})
                session.add(item)
                session.commit()
                session.refresh(item)

            # Create applications
            app_name = f"App {i}"
            app = session.exec(
                select(Application).where(Application.name == app_name)
            ).first()
            if not app:
                app_in = ApplicationCreate(
                    name=app_name,
                    description=f"This is app {i}",
                )
                app = Application.model_validate(app_in, update={"owner_id": user.id})
                session.add(app)
                session.commit()
                session.refresh(app)

        # Create groups
        users = session.exec(select(User).limit(10)).all()
        member_ids = [user.id for user in users]
        for i in range(1, 52):
            group_name = f"Group {i}"
            group = session.exec(select(Group).where(Group.name == group_name)).first()
            if not group:
                group_in = GroupCreate(
                    name=group_name,
                    description=f"This is group {i}",
                    member_ids=member_ids,
                )
                owner_id = member_ids[(i - 1) % len(member_ids)]
                group = Group.model_validate(group_in, update={"owner_id": owner_id})
                group.members = users
                session.add(group)
                session.commit()
                session.refresh(group)

    # 7. Create initial APIs from routes
    from app.api.main import api_router
    from app.model.api import Api, ApiCreate

    for route in api_router.routes:
        if hasattr(route, "methods"):
            for method in route.methods:
                if method in ["HEAD", "OPTIONS"]:
                    continue

                path = f"{settings.API_V1_STR}{route.path}"
                name = route.summary if route.summary else route.name
                group = route.tags[0] if route.tags else "default"

                existing_api = session.exec(
                    select(Api).where(Api.path == path).where(Api.method == method)
                ).first()

                if not existing_api:
                    api_in = ApiCreate(
                        group=group,
                        name=name,
                        path=path,
                        method=method,
                    )
                    api = Api.model_validate(api_in)
                    session.add(api)
                    session.commit()
                    session.refresh(api)
