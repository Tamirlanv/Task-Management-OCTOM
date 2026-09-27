from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Identifier, Timestamps


class Workspace(Identifier, Timestamps, Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        CheckConstraint("length(name) BETWEEN 1 AND 200", name="name_length"),
        CheckConstraint("length(description) <= 10000", name="description_length"),
    )

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
