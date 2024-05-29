import datetime
from enum import Enum

from typing import Any, Dict, List

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    DateTime,
)
from sqlalchemy.sql import func


Base = declarative_base()


class BaseModel:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    def as_dict(self, except_columns: List[str] = []) -> Dict[str, Any]:
        res = {}
        for c in self.__table__.columns:
            try:
                if c.name in ("password",):
                    continue
                if c.name in except_columns:
                    continue
                if isinstance(getattr(self, c.name), datetime.datetime) or isinstance(
                    getattr(self, c.name), datetime.date
                ):
                    res[c.name] = getattr(self, c.name).isoformat()
                else:
                    res[c.name] = getattr(self, c.name)
            except:
                continue
        return res

    @property
    def role_str(self) -> str:
        role_obj = [
            dr.name
            for _, dr in DefaultRoles.__members__.items()
            if dr.value == self.role
        ]
        if not role_obj:
            return ""
        return role_obj[0]


class AnonymousUser(BaseModel):
    id = 0
    username = "anonymous"
    password = ""
    role = 0

    @property
    def is_anonymous(self):
        return True


class DefaultRoles(Enum):
    operator = 0
    admin = 1
