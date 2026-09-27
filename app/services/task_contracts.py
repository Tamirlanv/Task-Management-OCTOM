from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from app.models.task import Task
from app.services.contracts import Priority, TaskStatus


@dataclass(frozen=True)
class TaskData:
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    due_at: datetime | None = None
    assignee_id: UUID | None = None
    tag_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class TaskChanges:
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    due_at: datetime | None = None
    assignee_id: UUID | None = None
    tag_ids: tuple[UUID, ...] | None = None
    replace_due: bool = False
    replace_assignee: bool = False


@dataclass(frozen=True)
class TaskQuery:
    limit: int = 20
    offset: int = 0
    project_id: UUID | None = None
    statuses: tuple[TaskStatus, ...] = ()
    priorities: tuple[Priority, ...] = ()
    assignee_id: UUID | None = None
    created_by: UUID | None = None
    tag_ids: tuple[UUID, ...] = ()
    unassigned: bool = False
    due_from: datetime | None = None
    due_to: datetime | None = None
    overdue: bool | None = None
    q: str | None = None
    sort: Literal["created_at", "updated_at", "due_at", "priority"] = "created_at"
    direction: Literal["asc", "desc"] = "desc"


@dataclass(frozen=True)
class TaskBundle:
    task: Task
    tag_ids: list[UUID]
