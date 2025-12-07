import hashlib

from sqlmodel import Session, or_, select

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.model.user import User, UserCreate, UserUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    # Ensure username is set
    if not user_create.username:
        user_create.username = user_create.email.split("@")[0]
    # Ensure unique username
    existing_user = get_user_by_username(session=session, username=user_create.username)
    if existing_user:
        suffix = 1
        base_username = user_create.username
        while True:
            new_username = f"{base_username}{suffix}"
            if not get_user_by_username(session=session, username=new_username):
                user_create.username = new_username
                break
            suffix += 1
    # Ensure avatar is set
    if not user_create.avatar:
        email_hash = hashlib.md5(
            user_create.email.lower().encode(encoding="utf-8")
        ).hexdigest()
        user_create.avatar = f"{settings.GRAVATAR_SOURCE}{email_hash}?d=identicon&s=256"
    # Create user
    db_obj = User.model_validate(
        user_create,
        update={
            "hashed_password": get_password_hash(user_create.password),
        },
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_update: UserUpdate) -> User:
    user_data = user_update.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_username(*, session: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    db_user = session.exec(statement).first()
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    db_user = session.exec(statement).first()
    return db_user


def get_user_by_username_or_email(
    *, session: Session, username: str, email: str
) -> User | None:
    statement = select(User).where(or_(User.username == username, User.email == email))
    db_user = session.exec(statement).first()
    return db_user


def delete_user(*, session: Session, db_user: User) -> None:
    session.delete(db_user)
    session.commit()


def authenticate(*, session: Session, username: str, password: str) -> User | None:
    db_user = get_user_by_username_or_email(
        session=session, username=username, email=username
    )
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user
