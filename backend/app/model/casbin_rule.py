from sqlmodel import Field, SQLModel


class CasbinRule(SQLModel, table=True):
    __tablename__ = "casbin_rules"

    id: int | None = Field(default=None, primary_key=True)
    ptype: str | None = Field(default=None, max_length=255)
    v0: str | None = Field(default=None, max_length=255)
    v1: str | None = Field(default=None, max_length=255)
    v2: str | None = Field(default=None, max_length=255)
    v3: str | None = Field(default=None, max_length=255)
    v4: str | None = Field(default=None, max_length=255)
    v5: str | None = Field(default=None, max_length=255)

    def __str__(self) -> str:
        arr = [self.ptype]
        for v in (self.v0, self.v1, self.v2, self.v3, self.v4, self.v5):
            if not v:
                break
            arr.append(v)
        return ", ".join(arr)
