from uuid import UUID

from app.models import Task
from app.repositories.protocols import UnitOfWork
from app.services.access import workspace_access
from app.services.contracts import TaskOwnership
from app.services.errors import InvalidInput, NotFound
from app.services.policies import (
    require_assignable,
    require_task_creation,
    require_task_edit,
)
from app.services.task_contracts import TaskBundle, TaskChanges, TaskData, TaskQuery
from app.services.task_rules import as_utc, validate_tag_ids, validate_task_filters


class TaskService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(
        self, workspace_id: UUID, project_id: UUID, actor_id: UUID, data: TaskData
    ) -> TaskBundle:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            await self._project(workspace_id, project_id)
            require_task_creation(actor)
            await self._relations(workspace_id, data.assignee_id, data.tag_ids)
            if data.due_at is not None:
                as_utc(data.due_at)
            task = await self.uow.tasks.create(workspace_id, project_id, actor_id, data)
            result = await self.uow.tasks.bundle(task)
            await self.uow.commit()
            return result

    async def get(
        self, workspace_id: UUID, task_id: UUID, actor_id: UUID
    ) -> TaskBundle:
        async with self.uow:
            await workspace_access(self.uow, workspace_id, actor_id)
            task = await self._get(workspace_id, task_id)
            result = await self.uow.tasks.bundle(task)
            await self.uow.commit()
            return result

    async def list(
        self, workspace_id: UUID, actor_id: UUID, filters: TaskQuery
    ) -> tuple[list[TaskBundle], int]:
        validate_task_filters(
            assignee_id=filters.assignee_id,
            unassigned=filters.unassigned,
            due_from=filters.due_from,
            due_to=filters.due_to,
        )
        async with self.uow:
            await workspace_access(self.uow, workspace_id, actor_id)
            if filters.project_id is not None:
                await self._project(workspace_id, filters.project_id)
            result = await self.uow.tasks.list(workspace_id, filters)
            await self.uow.commit()
            return result

    async def update(
        self, workspace_id: UUID, task_id: UUID, actor_id: UUID, changes: TaskChanges
    ) -> TaskBundle:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            task = await self._get(workspace_id, task_id)
            require_task_edit(
                actor, TaskOwnership(workspace_id, task.created_by, task.assignee_id)
            )
            await self._relations(
                workspace_id, changes.assignee_id, changes.tag_ids or ()
            )
            self._apply_changes(task, changes)
            if changes.tag_ids is not None:
                await self.uow.tasks.replace_tags(
                    workspace_id, task_id, changes.tag_ids
                )
            await self.uow.tasks.save(task)
            result = await self.uow.tasks.bundle(task)
            await self.uow.commit()
            return result

    async def remove(self, workspace_id: UUID, task_id: UUID, actor_id: UUID) -> None:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            task = await self._get(workspace_id, task_id)
            require_task_edit(
                actor, TaskOwnership(workspace_id, task.created_by, task.assignee_id)
            )
            await self.uow.tasks.remove(workspace_id, task_id)
            await self.uow.commit()

    async def _get(self, workspace_id: UUID, task_id: UUID) -> Task:
        task = await self.uow.tasks.get(workspace_id, task_id)
        if task is None:
            raise NotFound
        return task

    async def _project(self, workspace_id: UUID, project_id: UUID) -> None:
        if await self.uow.projects.get(workspace_id, project_id) is None:
            raise NotFound

    async def _relations(
        self, workspace_id: UUID, assignee_id: UUID | None, tag_ids: tuple[UUID, ...]
    ) -> None:
        if assignee_id is not None:
            require_assignable(
                await self.uow.memberships.get(workspace_id, assignee_id),
                workspace_id,
                assignee_id,
            )
        validate_tag_ids(tag_ids)
        if tag_ids and await self.uow.tags.count_ids(workspace_id, tag_ids) != len(
            tag_ids
        ):
            raise InvalidInput

    @staticmethod
    def _apply_changes(task: Task, changes: TaskChanges) -> None:
        if changes.title is not None:
            task.title = changes.title
        if changes.description is not None:
            task.description = changes.description
        if changes.status is not None:
            task.status = changes.status.value
        if changes.priority is not None:
            task.priority = changes.priority.value
        if changes.replace_due:
            task.due_at = as_utc(changes.due_at) if changes.due_at is not None else None
        if changes.replace_assignee:
            task.assignee_id = changes.assignee_id
