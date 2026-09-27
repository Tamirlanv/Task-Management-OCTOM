from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Identifier, Timestamps


class Task(Identifier, Timestamps, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        ForeignKeyConstraint(
            ["workspace_id", "project_id"],
            ["projects.workspace_id", "projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "assignee_id"],
            ["workspace_memberships.workspace_id", "workspace_memberships.user_id"],
        ),
        CheckConstraint("length(title) BETWEEN 1 AND 200", name="title_length"),
        CheckConstraint("length(description) <= 10000", name="description_length"),
        CheckConstraint(
            "status IN ('todo', 'in_progress', 'done', 'cancelled')",
            name="valid_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')", name="valid_priority"
        ),
        Index(
            "ix_tasks_workspace_project_created",
            "workspace_id",
            "project_id",
            "created_at",
            "id",
        ),
        Index("ix_tasks_workspace_status", "workspace_id", "status"),
        Index("ix_tasks_workspace_assignee", "workspace_id", "assignee_id"),
        Index("ix_tasks_workspace_due", "workspace_id", "due_at"),
        Index(
            "ix_tasks_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
        Index(
            "ix_tasks_description_trgm",
            "description",
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
        ),
    )

    workspace_id: Mapped[UUID]
    project_id: Mapped[UUID]
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    status: Mapped[str] = mapped_column(
        String(20), default="todo", server_default="todo"
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="medium", server_default="medium"
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    assignee_id: Mapped[UUID | None]
