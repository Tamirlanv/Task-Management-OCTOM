from uuid import UUID

from app.models import Project
from app.repositories.protocols import UnitOfWork
from app.services.access import workspace_access
from app.services.errors import NotFound
from app.services.policies import require_project_management


class ProjectService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(
        self, workspace_id: UUID, actor_id: UUID, name: str, description: str
    ) -> Project:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            require_project_management(actor)
            project = await self.uow.projects.create(
                workspace_id, actor_id, name, description
            )
            await self.uow.commit()
            return project

    async def list(
        self, workspace_id: UUID, actor_id: UUID, limit: int, offset: int
    ) -> tuple[list[Project], int]:
        async with self.uow:
            await workspace_access(self.uow, workspace_id, actor_id)
            result = await self.uow.projects.list(workspace_id, limit, offset)
            await self.uow.commit()
            return result

    async def get(
        self, workspace_id: UUID, actor_id: UUID, project_id: UUID
    ) -> Project:
        async with self.uow:
            await workspace_access(self.uow, workspace_id, actor_id)
            project = await self._get(workspace_id, project_id)
            await self.uow.commit()
            return project

    async def update(
        self,
        workspace_id: UUID,
        actor_id: UUID,
        project_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Project:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            project = await self._get(workspace_id, project_id)
            require_project_management(actor)
            if name is not None:
                project.name = name
            if description is not None:
                project.description = description
            await self.uow.projects.save(project)
            await self.uow.commit()
            return project

    async def remove(
        self, workspace_id: UUID, actor_id: UUID, project_id: UUID
    ) -> None:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            await self._get(workspace_id, project_id)
            require_project_management(actor)
            await self.uow.projects.remove(workspace_id, project_id)
            await self.uow.commit()

    async def _get(self, workspace_id: UUID, project_id: UUID) -> Project:
        project = await self.uow.projects.get(workspace_id, project_id)
        if project is None:
            raise NotFound
        return project
