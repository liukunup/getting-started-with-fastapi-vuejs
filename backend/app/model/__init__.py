from sqlmodel import SQLModel

from app.model.api import *
from app.model.application import *
from app.model.base import *
from app.model.casbin_rule import *
from app.model.group import *
from app.model.item import *
from app.model.link import *
from app.model.menu import *
from app.model.system_setting import *
from app.model.task import *
from app.model.task_execution import *
from app.model.user import *

__all__ = ["SQLModel"]
