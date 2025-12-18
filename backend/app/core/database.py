import logging

from sqlmodel import Session, and_, create_engine, select

from app import crud
from app.core.config import settings
from app.model import (
    Api,
    ApiCreate,
    Application,
    ApplicationCreate,
    Group,
    GroupCreate,
    Item,
    ItemCreate,
    Menu,
    MenuCreate,
    Role,
    User,
    UserCreate,
)

logger = logging.getLogger(__name__)

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
    logger.info("Initializing database with initial data...")
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    # 1. Create initial roles
    logger.info("1/7 Creating initial roles...")
    for role_name in ["admin", "user", "guest"]:
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        if not role:
            role = Role(name=role_name, description=role_name.capitalize())
            session.add(role)
            session.commit()

    # 2. Create initial superuser
    logger.info("2/7 Creating initial superuser...")
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            role_id=admin_role.id if admin_role else None,
        )
        user = crud.create_user(session=session, user_create=user_in)

    # 3. Create initial APIs from routes
    logger.info("3/7 Creating initial APIs from routes...")
    from app.api.main import api_router

    # Fetch all routes from api_router
    for route in api_router.routes:
        if hasattr(route, "methods"):
            for method in route.methods:
                # Skip HEAD and OPTIONS methods
                if method in ["HEAD", "OPTIONS"]:
                    continue
                # Construct API path / name / group
                path = f"{settings.API_V1_STR}{route.path}"
                name = route.summary if route.summary else route.name
                group = route.tags[0] if route.tags else "default"
                # Check if API already exists
                existing_api = session.exec(
                    select(Api).where(and_(Api.path == path, Api.method == method))
                ).first()
                if not existing_api:
                    api_in = ApiCreate(
                        group=group,
                        name=name,
                        path=path,
                        method=method,
                    )
                    # Create API
                    api = Api.model_validate(api_in, update={"owner_id": user.id})
                    session.add(api)
                    session.commit()

    # 4. Create initial casbin policies for api access control
    logger.info("4/7 Creating initial casbin policies for api access control...")
    from app.core.casbin import enforcer

    # Guest policies
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/login/config", "GET")
    enforcer.add_policy(
        "api:guest", f"{settings.API_V1_STR}/login/access-token", "POST"
    )
    enforcer.add_policy(
        "api:guest", f"{settings.API_V1_STR}/password-recovery/*", "POST"
    )
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/reset-password/", "POST")
    enforcer.add_policy(
        "api:guest", f"{settings.API_V1_STR}/password-recovery-html-content/", "POST"
    )
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/register", "POST")
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/users/signup", "POST")
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/login/oidc", "POST")
    enforcer.add_policy(
        "api:guest", f"{settings.API_V1_STR}/login/oidc/callback", "POST"
    )
    enforcer.add_policy("api:guest", f"{settings.API_V1_STR}/logout/oidc", "POST")

    # Allow api:user to inherit api:guest permissions
    enforcer.add_grouping_policy("api:user", "api:guest")

    # User policies
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/users*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/items*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/groups*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/app*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/tasks*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/utils*", "*")
    enforcer.add_policy("api:user", f"{settings.API_V1_STR}/openapi*", "*")
    # Admin policies
    # Usually admin has all permissions, handled by is_superuser check or wildcard policy
    enforcer.add_policy("api:admin", "/*", "*")

    # 5. Create initial menus
    logger.info("5/7 Creating initial menus...")
    initial_main_menu_structure = [
        {
            "label": "Home",
            "name": "home",
            "items": [
                {
                    "label": "Dashboard",
                    "icon": "pi pi-fw pi-home",
                    "to": "/",
                    "name": "dashboard",
                    "component": "@/views/Dashboard.vue",
                },
                {
                    "label": "Items",
                    "icon": "pi pi-fw pi-list",
                    "to": "/items",
                    "name": "items",
                    "component": "@/views/business/Items.vue",
                },
                {
                    "label": "Groups",
                    "icon": "pi pi-fw pi-users",
                    "to": "/groups",
                    "name": "groups",
                    "component": "@/views/business/Groups.vue",
                },
                {
                    "label": "Applications",
                    "icon": "pi pi-fw pi-box",
                    "to": "/applications",
                    "name": "applications",
                    "component": "@/views/business/Applications.vue",
                },
                {
                    "label": "Tasks",
                    "icon": "pi pi-fw pi-clock",
                    "to": "/tasks",
                    "name": "tasks",
                    "component": "@/views/business/Tasks.vue",
                },
                {
                    "label": "Task Executions",
                    "icon": "pi pi-fw pi-history",
                    "to": "/task-executions",
                    "name": "task-executions",
                    "component": "@/views/business/TaskExecutions.vue",
                },
                {
                    "label": "Profile",
                    "icon": "pi pi-fw pi-user",
                    "to": "/profile",
                    "name": "profile",
                    "component": "@/views/pages/Profile.vue",
                },
            ],
        }
    ]
    initial_admin_menu_structure = [
        {
            "label": "Admin",
            "name": "admin",
            "items": [
                {
                    "label": "Celery",
                    "icon": "pi pi-fw pi-server",
                    "to": "/admin/celery",
                    "name": "celery",
                    "component": "@/views/pages/admin/Celery.vue",
                },
                {
                    "label": "Menus",
                    "icon": "pi pi-fw pi-bars",
                    "to": "/admin/menus",
                    "name": "menus",
                    "component": "@/views/pages/admin/Menus.vue",
                },
                {
                    "label": "APIs",
                    "icon": "pi pi-fw pi-tags",
                    "to": "/admin/apis",
                    "name": "apis",
                    "component": "@/views/pages/admin/Apis.vue",
                },
                {
                    "label": "Roles",
                    "icon": "pi pi-fw pi-id-card",
                    "to": "/admin/roles",
                    "name": "roles",
                    "component": "@/views/pages/admin/Roles.vue",
                },
                {
                    "label": "Users",
                    "icon": "pi pi-fw pi-users",
                    "to": "/admin/users",
                    "name": "users",
                    "component": "@/views/pages/admin/Users.vue",
                },
                {
                    "label": "Settings",
                    "icon": "pi pi-fw pi-cog",
                    "to": "/admin/settings",
                    "name": "settings",
                    "component": "@/views/pages/admin/Settings.vue",
                },
            ],
        }
    ]
    initial_dev_menu_structure = [
        {
            "label": "UI Components",
            "name": "ui-components",
            "items": [
                {
                    "label": "Form Layout",
                    "icon": "pi pi-fw pi-id-card",
                    "to": "/uikit/formlayout",
                    "name": "form-layout",
                    "component": "@/views/uikit/FormLayout.vue",
                },
                {
                    "label": "Input",
                    "icon": "pi pi-fw pi-check-square",
                    "to": "/uikit/input",
                    "name": "input",
                    "component": "@/views/uikit/InputDoc.vue",
                },
                {
                    "label": "Button",
                    "icon": "pi pi-fw pi-mobile",
                    "to": "/uikit/button",
                    "class": "rotated-icon",
                    "name": "button",
                    "component": "@/views/uikit/ButtonDoc.vue",
                },
                {
                    "label": "Table",
                    "icon": "pi pi-fw pi-table",
                    "to": "/uikit/table",
                    "name": "table",
                    "component": "@/views/uikit/TableDoc.vue",
                },
                {
                    "label": "List",
                    "icon": "pi pi-fw pi-list",
                    "to": "/uikit/list",
                    "name": "list",
                    "component": "@/views/uikit/ListDoc.vue",
                },
                {
                    "label": "Tree",
                    "icon": "pi pi-fw pi-share-alt",
                    "to": "/uikit/tree",
                    "name": "tree",
                    "component": "@/views/uikit/TreeDoc.vue",
                },
                {
                    "label": "Panel",
                    "icon": "pi pi-fw pi-tablet",
                    "to": "/uikit/panel",
                    "name": "panel",
                    "component": "@/views/uikit/PanelsDoc.vue",
                },
                {
                    "label": "Overlay",
                    "icon": "pi pi-fw pi-clone",
                    "to": "/uikit/overlay",
                    "name": "overlay",
                    "component": "@/views/uikit/OverlayDoc.vue",
                },
                {
                    "label": "Media",
                    "icon": "pi pi-fw pi-image",
                    "to": "/uikit/media",
                    "name": "media",
                    "component": "@/views/uikit/MediaDoc.vue",
                },
                {
                    "label": "Menu",
                    "icon": "pi pi-fw pi-bars",
                    "to": "/uikit/menu",
                    "name": "menu",
                    "component": "@/views/uikit/MenuDoc.vue",
                },
                {
                    "label": "Message",
                    "icon": "pi pi-fw pi-comment",
                    "to": "/uikit/message",
                    "name": "message",
                    "component": "@/views/uikit/MessagesDoc.vue",
                },
                {
                    "label": "File",
                    "icon": "pi pi-fw pi-file",
                    "to": "/uikit/file",
                    "name": "file",
                    "component": "@/views/uikit/FileDoc.vue",
                },
                {
                    "label": "Chart",
                    "icon": "pi pi-fw pi-chart-bar",
                    "to": "/uikit/charts",
                    "name": "chart",
                    "component": "@/views/uikit/ChartDoc.vue",
                },
                {
                    "label": "Timeline",
                    "icon": "pi pi-fw pi-calendar",
                    "to": "/uikit/timeline",
                    "name": "timeline",
                    "component": "@/views/uikit/TimelineDoc.vue",
                },
                {
                    "label": "Misc",
                    "icon": "pi pi-fw pi-circle",
                    "to": "/uikit/misc",
                    "name": "misc",
                    "component": "@/views/uikit/MiscDoc.vue",
                },
            ],
        },
        {
            "label": "Prime Blocks",
            "name": "prime-blocks",
            "icon": "pi pi-fw pi-prime",
            "items": [
                {
                    "label": "Free Blocks",
                    "icon": "pi pi-fw pi-eye",
                    "to": "/blocks",
                    "name": "free-blocks",
                    "component": "@/views/utilities/Blocks.vue",
                },
                {
                    "label": "All Blocks",
                    "icon": "pi pi-fw pi-globe",
                    "url": "https://blocks.primevue.org/",
                    "target": "_blank",
                    "name": "all-blocks",
                },
            ],
        },
        {
            "label": "Pages",
            "name": "pages",
            "icon": "pi pi-fw pi-briefcase",
            "to": "/pages",
            "items": [
                {
                    "label": "Landing",
                    "icon": "pi pi-fw pi-globe",
                    "to": "/landing",
                    "name": "landing",
                    "component": "@/views/pages/Landing.vue",
                },
                {
                    "label": "Auth",
                    "name": "auth",
                    "icon": "pi pi-fw pi-user",
                    "items": [
                        {
                            "label": "Login",
                            "icon": "pi pi-fw pi-sign-in",
                            "to": "/auth/login",
                            "name": "login",
                            "component": "@/views/pages/auth/Login.vue",
                        },
                        {
                            "label": "Register",
                            "icon": "pi pi-fw pi-user-plus",
                            "to": "/auth/register",
                            "name": "register",
                            "component": "@/views/pages/auth/Register.vue",
                        },
                        {
                            "label": "Forgot Password",
                            "icon": "pi pi-fw pi-key",
                            "to": "/auth/forgot-password",
                            "name": "forgot-password",
                            "component": "@/views/pages/auth/ForgotPassword.vue",
                        },
                        {
                            "label": "Reset Password",
                            "icon": "pi pi-fw pi-refresh",
                            "to": "/auth/reset-password",
                            "name": "reset-password",
                            "component": "@/views/pages/auth/ResetPassword.vue",
                        },
                        {
                            "label": "Error",
                            "icon": "pi pi-fw pi-times-circle",
                            "to": "/auth/error",
                            "name": "error",
                            "component": "@/views/pages/auth/Error.vue",
                        },
                        {
                            "label": "Access Denied",
                            "icon": "pi pi-fw pi-lock",
                            "to": "/auth/access",
                            "name": "access-denied",
                            "component": "@/views/pages/auth/Access.vue",
                        },
                    ],
                },
                {
                    "label": "Crud",
                    "icon": "pi pi-fw pi-pencil",
                    "to": "/pages/crud",
                    "name": "crud",
                    "component": "@/views/pages/Crud.vue",
                },
                {
                    "label": "Not Found",
                    "icon": "pi pi-fw pi-exclamation-circle",
                    "to": "/pages/notfound",
                    "name": "not-found",
                    "component": "@/views/pages/NotFound.vue",
                },
                {
                    "label": "Empty",
                    "icon": "pi pi-fw pi-circle-off",
                    "to": "/pages/empty",
                    "name": "empty",
                    "component": "@/views/pages/Empty.vue",
                },
            ],
        },
        {
            "label": "Hierarchy",
            "name": "hierarchy",
            "items": [
                {
                    "label": "Submenu 1",
                    "name": "submenu-1",
                    "icon": "pi pi-fw pi-bookmark",
                    "items": [
                        {
                            "label": "Submenu 1.1",
                            "name": "submenu-1-1",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 1.1.1",
                                    "name": "submenu-1-1-1",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                                {
                                    "label": "Submenu 1.1.2",
                                    "name": "submenu-1-1-2",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                                {
                                    "label": "Submenu 1.1.3",
                                    "name": "submenu-1-1-3",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                            ],
                        },
                        {
                            "label": "Submenu 1.2",
                            "name": "submenu-1-2",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 1.2.1",
                                    "name": "submenu-1-2-1",
                                    "icon": "pi pi-fw pi-bookmark",
                                }
                            ],
                        },
                    ],
                },
                {
                    "label": "Submenu 2",
                    "name": "submenu-2",
                    "icon": "pi pi-fw pi-bookmark",
                    "items": [
                        {
                            "label": "Submenu 2.1",
                            "name": "submenu-2-1",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 2.1.1",
                                    "name": "submenu-2-1-1",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                                {
                                    "label": "Submenu 2.1.2",
                                    "name": "submenu-2-1-2",
                                    "icon": "pi pi-fw pi-bookmark",
                                },
                            ],
                        },
                        {
                            "label": "Submenu 2.2",
                            "name": "submenu-2-2",
                            "icon": "pi pi-fw pi-bookmark",
                            "items": [
                                {
                                    "label": "Submenu 2.2.1",
                                    "name": "submenu-2-2-1",
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
            "name": "get-started",
            "items": [
                {
                    "label": "Documentation",
                    "name": "documentation",
                    "icon": "pi pi-fw pi-book",
                    "to": "/documentation",
                    "component": "@/views/pages/Documentation.vue",
                },
                {
                    "label": "View Source",
                    "name": "view-source",
                    "icon": "pi pi-fw pi-github",
                    "url": "https://github.com/primefaces/sakai-vue",
                    "target": "_blank",
                },
            ],
        },
    ]

    def create_menu_recursive(menu_data, parent_id=None):
        """Recursively create menu items."""
        name = menu_data.get("name")
        statement = select(Menu).where(Menu.name == name)
        if parent_id:
            statement = statement.where(Menu.parent_id == parent_id)
        else:
            statement = statement.where(Menu.parent_id == None)  # noqa: E711
        # Check if menu already exists
        existing_menu = session.exec(statement).first()
        if not existing_menu:
            menu_in = MenuCreate(
                name=name,
                path=menu_data.get("to"),
                component=menu_data.get("component"),
                label=menu_data.get("label"),
                icon=menu_data.get("icon"),
                to=menu_data.get("to"),
                url=menu_data.get("url"),
                target=menu_data.get("target"),
                clazz=menu_data.get("class"),
                parent_id=parent_id,
            )
            # Create menu
            existing_menu = Menu.model_validate(menu_in, update={"owner_id": user.id})
            session.add(existing_menu)
            session.commit()
            session.refresh(existing_menu)

        # Recursively create child items
        if "items" in menu_data:
            for item in menu_data["items"]:
                create_menu_recursive(item, parent_id=existing_menu.id)

    # Create main menus
    for menu in initial_main_menu_structure:
        create_menu_recursive(menu)

    # Create admin menus
    for admin_menu in initial_admin_menu_structure:
        create_menu_recursive(admin_menu)

    # Add dev menus only in local environment
    if settings.ENVIRONMENT == "local":
        for dev_menu in initial_dev_menu_structure:
            create_menu_recursive(dev_menu)

    # 6. Create initial casbin policies for menu access control
    logger.info("6/7 Creating initial casbin policies for menu access control...")
    # Guest policies
    guest_menus = ["login", "register", "forgot-password", "reset-password"]
    for menu_name in guest_menus:
        enforcer.add_policy("menu:guest", menu_name, "visible")
    # User policies
    user_menus = [
        "home",
        "dashboard",
        "items",
        "groups",
        "applications",
        "tasks",
        "task-executions",
        "profile",
    ]
    for menu_name in user_menus:
        enforcer.add_policy("menu:user", menu_name, "visible")
    # Admin policies
    admin_menus = [
        "home",
        "dashboard",
        "items",
        "groups",
        "applications",
        "tasks",
        "task-executions",
        "profile",
        "admin",
        "celery",
        "menus",
        "apis",
        "roles",
        "users",
        "settings",
    ]
    for menu_name in admin_menus:
        enforcer.add_policy("menu:admin", menu_name, "visible")

    # 7. Create initial data for dev & testing
    logger.info("7/7 Creating initial data for dev & testing...")
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
                    description=f"This is item {i}. Longer description to test text wrapping in the UI.",
                )
                item = Item.model_validate(item_in, update={"owner_id": user.id})
                session.add(item)
                session.commit()

            # Create applications
            app_name = f"App {i}"
            app = session.exec(
                select(Application).where(Application.name == app_name)
            ).first()
            if not app:
                app_in = ApplicationCreate(
                    name=app_name,
                    description=f"This is app {i}. Longer description to test text wrapping in the UI.",
                )
                app = Application.model_validate(app_in, update={"owner_id": user.id})
                session.add(app)
                session.commit()

        # Create groups
        users = session.exec(select(User).limit(10)).all()
        member_ids = [user.id for user in users]
        for i in range(1, 52):
            group_name = f"Group {i}"
            group = session.exec(select(Group).where(Group.name == group_name)).first()
            if not group:
                group_in = GroupCreate(
                    name=group_name,
                    description=f"This is group {i}. Longer description to test text wrapping in the UI.",
                    member_ids=member_ids,
                )
                owner_id = member_ids[(i - 1) % len(member_ids)]
                group = Group.model_validate(group_in, update={"owner_id": owner_id})
                group.members = users
                session.add(group)
                session.commit()

    logger.info("Database initialization complete.")
