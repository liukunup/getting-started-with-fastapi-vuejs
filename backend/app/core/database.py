from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.model.application import Application, ApplicationCreate
from app.model.group import Group, GroupCreate
from app.model.item import Item, ItemCreate
from app.model.user import User, UserCreate

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

    # Create initial super user
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

    # Create initial data for dev & testing
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
                session.add(group)
                session.commit()
                session.refresh(group)
