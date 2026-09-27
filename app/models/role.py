from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Identifier


class RoleModel(Identifier, Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint(
            "name IN ('Admin', 'Manager', 'Member', 'Viewer')", name="valid_role"
        ),
    )

    name: Mapped[str] = mapped_column(String(20), unique=True)
