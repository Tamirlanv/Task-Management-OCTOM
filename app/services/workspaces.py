from uuid import UUID

from app.models.workspace import Workspace
from app.repositories.protocols import UnitOfWork
from app.services.access import workspace_access
from app.services.contracts import Role
from app.services.policies import require_admin


class WorkspaceService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(self, actor_id: UUID, name: str, description: str) -> Workspace:
        async with self.uow:
            workspace = await self.uow.workspaces.create(name, description)
            await self.uow.memberships.add(workspace.id, actor_id, Role.ADMIN)
            await self.uow.commit()
            return workspace

    async def list(
        self, actor_id: UUID, limit: int, offset: int
    ) -> tuple[list[Workspace], int]:
        async with self.uow:
            result = await self.uow.workspaces.list(actor_id, limit, offset)
            await self.uow.commit()
            return result

    async def get(self, workspace_id: UUID, actor_id: UUID) -> Workspace:
        async with self.uow:
            workspace, _ = await workspace_access(self.uow, workspace_id, actor_id)
            await self.uow.commit()
            return workspace

    async def update(
        self,
        workspace_id: UUID,
        actor_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Workspace:
        async with self.uow:
            workspace, member = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            require_admin(member)
            if name is not None:
                workspace.name = name
            if description is not None:
                workspace.description = description
            await self.uow.workspaces.save(workspace)
            await self.uow.commit()
            return workspace

    async def remove(self, workspace_id: UUID, actor_id: UUID) -> None:
        async with self.uow:
            _, member = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            require_admin(member)
            await self.uow.workspaces.remove(workspace_id)
            await self.uow.commit()
