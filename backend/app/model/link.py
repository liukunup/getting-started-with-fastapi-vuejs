import uuid

from sqlmodel import Field, SQLModel


class GroupMemberLink(SQLModel, table=True):
    __tablename__ = "group_member_link"

    group_id: uuid.UUID = Field(foreign_key="groups.id", primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
