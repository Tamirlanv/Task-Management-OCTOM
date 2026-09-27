import builtins
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, TaskTag
from app.repositories.task_queries import filtered_tasks, sorted_tasks
from app.services.task_contracts import TaskBundle, TaskData, TaskQuery


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, workspace_id: UUID, task_id: UUID) -> Task | None:
        return (
            await self.session.scalars(
                select(Task).where(
                    Task.workspace_id == workspace_id, Task.id == task_id
                )
            )
        ).one_or_none()

    async def list(
        self, workspace_id: UUID, filters: TaskQuery
    ) -> tuple[list[TaskBundle], int]:
        query = filtered_tasks(workspace_id, filters)
        total = await self.session.scalar(
            select(func.count()).select_from(query.subquery())
        )
        tasks = list(await self.session.scalars(sorted_tasks(query, filters)))
        tags = await self._tags(workspace_id, [task.id for task in tasks])
        return [TaskBundle(task, tags.get(task.id, [])) for task in tasks], int(
            total or 0
        )

    async def create(
        self, workspace_id: UUID, project_id: UUID, actor_id: UUID, data: TaskData
    ) -> Task:
        task = Task(
            workspace_id=workspace_id,
            project_id=project_id,
            created_by=actor_id,
            title=data.title,
            description=data.description,
            status=data.status.value,
            priority=data.priority.value,
            due_at=data.due_at,
            assignee_id=data.assignee_id,
        )
        self.session.add(task)
        await self.session.flush()
        await self.replace_tags(workspace_id, task.id, data.tag_ids)
        return task

    async def bundle(self, task: Task) -> TaskBundle:
        tags = await self._tags(task.workspace_id, [task.id])
        return TaskBundle(task, tags.get(task.id, []))

    async def save(self, task: Task) -> None:
        await self.session.flush()
        await self.session.refresh(task)

    async def replace_tags(
        self, workspace_id: UUID, task_id: UUID, tag_ids: tuple[UUID, ...]
    ) -> None:
        await self.session.execute(
            delete(TaskTag).where(
                TaskTag.workspace_id == workspace_id, TaskTag.task_id == task_id
            )
        )
        self.session.add_all(
            [
                TaskTag(workspace_id=workspace_id, task_id=task_id, tag_id=tag)
                for tag in tag_ids
            ]
        )
        await self.session.flush()

    async def remove(self, workspace_id: UUID, task_id: UUID) -> None:
        await self.session.execute(
            delete(Task).where(Task.workspace_id == workspace_id, Task.id == task_id)
        )

    async def _tags(
        self, workspace_id: UUID, task_ids: builtins.list[UUID]
    ) -> dict[UUID, builtins.list[UUID]]:
        if not task_ids:
            return {}
        rows = await self.session.execute(
            select(TaskTag.task_id, TaskTag.tag_id)
            .where(TaskTag.workspace_id == workspace_id, TaskTag.task_id.in_(task_ids))
            .order_by(TaskTag.tag_id)
        )
        result: dict[UUID, builtins.list[UUID]] = {}
        for task_id, tag_id in rows:
            result.setdefault(task_id, []).append(tag_id)
        return result
