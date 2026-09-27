from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    MEMBER = "Member"
    VIEWER = "Viewer"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    @property
    def rank(self) -> int:
        return list(Priority).index(self)


@dataclass(frozen=True, slots=True)
class Membership:
    workspace_id: UUID
    user_id: UUID
    role: Role


@dataclass(frozen=True, slots=True)
class TaskOwnership:
    workspace_id: UUID
    created_by: UUID
    assignee_id: UUID | None = None
