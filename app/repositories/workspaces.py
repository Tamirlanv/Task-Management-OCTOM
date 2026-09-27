from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, Workspace, WorkspaceMembership


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, workspace_id: UUID, *, lock: bool = False) -> Workspace | None:
        query = select(Workspace).where(Workspace.id == workspace_id)
        if lock:
            query = query.with_for_update()
        return (await self.session.scalars(query)).one_or_none()

    async def list(
        self, actor_id: UUID, limit: int, offset: int
    ) -> tuple[list[Workspace], int]:
        query = (
            select(Workspace)
            .join(WorkspaceMembership)
            .where(WorkspaceMembership.user_id == actor_id)
        )
        total = await self.session.scalar(
            select(func.count()).select_from(query.subquery())
        )
        items = await self.session.scalars(
            query.order_by(Workspace.created_at.desc(), Workspace.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(items), int(total or 0)

    async def create(self, name: str, description: str) -> Workspace:
        workspace = Workspace(name=name, description=description)
        self.session.add(workspace)
        await self.session.flush()
        return workspace

    async def save(self, workspace: Workspace) -> None:
        await self.session.flush()
        await self.session.refresh(workspace)

    async def remove(self, workspace_id: UUID) -> None:
        # Remove task assignment FKs before cascading through workspace memberships.
        await self.session.execute(
            delete(Task).where(Task.workspace_id == workspace_id)
        )
        await self.session.execute(
            delete(Workspace).where(Workspace.id == workspace_id)
        )
