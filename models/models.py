from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    Boolean,
    Integer,
    String,
    UniqueConstraint,
    Text,
    ForeignKey,
)
from sqlalchemy.sql import expression
from sqlalchemy.dialects import postgresql

from .base import Base, BaseModel, TaskStatus


class User(Base, BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    blocked: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, default=False, server_default=expression.false()
    )
    role: Mapped[int] = mapped_column(Integer(), default=1, server_default="1")  # DefaultRoles

    @property
    def is_anonymous(self):
        return False


class Provider(Base, BaseModel):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    auth_token: Mapped[str] = mapped_column(
        String(2048), nullable=False
    )
    accessed_role: Mapped[int] = mapped_column(Integer(), default=0, server_default="0")  # DefaultRoles

    __table_args__ = (
        UniqueConstraint("name", "auth_token", name="uc_name_auth_token"),
    )


class ParsingTasks(Base, BaseModel):
    __tablename__ = "parsing_tasks"

    id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, autoincrement=True
    )
    task_id: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    filename: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Integer(), nullable=False, default=TaskStatus.pending, server_default="0"
    )

    @property
    def status_str(self) -> str:
        for v in TaskStatus.__members__.values():
            if v.value == self.status:
                return v.name
        return ""
