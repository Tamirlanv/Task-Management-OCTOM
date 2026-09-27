from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Identifier


class Tag(Identifier, Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        CheckConstraint("length(name) BETWEEN 1 AND 50", name="name_length"),
        CheckConstraint(
            "color IS NULL OR color ~ '^#[0-9a-fA-F]{6}$'", name="color_format"
        ),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(7))


Index("uq_tags_workspace_name", Tag.workspace_id, func.lower(Tag.name), unique=True)


class TaskTag(Base):
    __tablename__ = "task_tags"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "task_id"],
            ["tasks.workspace_id", "tasks.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "tag_id"],
            ["tags.workspace_id", "tags.id"],
            ondelete="CASCADE",
        ),
        Index("ix_task_tags_tag_id", "tag_id"),
    )

    task_id: Mapped[UUID] = mapped_column(primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(primary_key=True)
    workspace_id: Mapped[UUID]
