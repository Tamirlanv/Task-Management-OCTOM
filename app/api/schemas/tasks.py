from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.api.schemas.common import Description, InputModel, Name, Pagination, PatchModel
from app.services.contracts import Priority, TaskStatus
from app.services.task_contracts import TaskBundle, TaskChanges, TaskData, TaskQuery

TagIds = Annotated[list[UUID], Field(max_length=20)]


class TaskCreate(InputModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Prepare release notes",
                    "description": "Document the API changes",
                    "status": "todo",
                    "priority": "high",
                    "due_at": "2026-10-10T12:00:00Z",
                    "assignee_id": None,
                    "tag_ids": [],
                }
            ]
        }
    )
    title: Name
    description: Description = ""
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    due_at: AwareDatetime | None = None
    assignee_id: UUID | None = None
    tag_ids: TagIds = Field(default_factory=list)

    def command(self) -> TaskData:
        return TaskData(
            self.title,
            self.description,
            self.status,
            self.priority,
            self.due_at,
            self.assignee_id,
            tuple(self.tag_ids),
        )


class TaskUpdate(PatchModel):
    title: Name | None = None
    description: Description | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    due_at: AwareDatetime | None = None
    assignee_id: UUID | None = None
    tag_ids: TagIds | None = None

    def command(self) -> TaskChanges:
        return TaskChanges(
            self.title,
            self.description,
            self.status,
            self.priority,
            self.due_at,
            self.assignee_id,
            tuple(self.tag_ids) if self.tag_ids is not None else None,
            "due_at" in self.model_fields_set,
            "assignee_id" in self.model_fields_set,
        )


class TaskFilters(Pagination):
    project_id: UUID | None = None
    statuses: list[TaskStatus] = Field(default_factory=list)
    priorities: list[Priority] = Field(default_factory=list)
    assignee_id: UUID | None = None
    created_by: UUID | None = None
    tag_ids: TagIds = Field(default_factory=list)
    unassigned: bool = False
    due_from: AwareDatetime | None = None
    due_to: AwareDatetime | None = None
    overdue: bool | None = None
    q: str | None = Field(default=None, min_length=1, max_length=200)
    sort: Literal["created_at", "updated_at", "due_at", "priority"] = "created_at"
    direction: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def consistent_filters(self) -> Self:
        if self.unassigned and self.assignee_id is not None:
            raise ValueError("unassigned and assignee_id are mutually exclusive")
        if (
            self.due_from is not None
            and self.due_to is not None
            and self.due_from > self.due_to
        ):
            raise ValueError("due_from must not be after due_to")
        return self

    def command(self) -> TaskQuery:
        return TaskQuery(
            limit=self.limit,
            offset=self.offset,
            project_id=self.project_id,
            statuses=tuple(self.statuses),
            priorities=tuple(self.priorities),
            assignee_id=self.assignee_id,
            created_by=self.created_by,
            tag_ids=tuple(self.tag_ids),
            unassigned=self.unassigned,
            due_from=self.due_from,
            due_to=self.due_to,
            overdue=self.overdue,
            q=self.q,
            sort=self.sort,
            direction=self.direction,
        )


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    priority: Priority
    due_at: datetime | None
    created_by: UUID
    assignee_id: UUID | None
    created_at: datetime
    updated_at: datetime
    tag_ids: list[UUID] = Field(default_factory=list)

    @classmethod
    def from_bundle(cls, bundle: TaskBundle) -> Self:
        result = cls.model_validate(bundle.task)
        result.tag_ids = bundle.tag_ids
        return result
