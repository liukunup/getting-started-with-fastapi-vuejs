from sqlmodel import SQLModel

from app.model.application import *
from app.model.base import *
from app.model.group import *
from app.model.item import *
from app.model.link import *
from app.model.user import *

__all__ = [SQLModel]
