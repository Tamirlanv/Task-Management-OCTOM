from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, workspace_id: UUID, project_id: UUID) -> Project | None:
        return (
            await self.session.scalars(
                select(Project).where(
                    Project.workspace_id == workspace_id, Project.id == project_id
                )
            )
        ).one_or_none()

    async def list(
        self, workspace_id: UUID, limit: int, offset: int
    ) -> tuple[list[Project], int]:
        query = select(Project).where(Project.workspace_id == workspace_id)
        total = await self.session.scalar(
            select(func.count()).select_from(query.subquery())
        )
        items = await self.session.scalars(
            query.order_by(Project.created_at.desc(), Project.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(items), int(total or 0)

    async def create(
        self, workspace_id: UUID, actor_id: UUID, name: str, description: str
    ) -> Project:
        project = Project(
            workspace_id=workspace_id,
            created_by=actor_id,
            name=name,
            description=description,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def save(self, project: Project) -> None:
        await self.session.flush()
        await self.session.refresh(project)

    async def remove(self, workspace_id: UUID, project_id: UUID) -> None:
        await self.session.execute(
            delete(Project).where(
                Project.workspace_id == workspace_id, Project.id == project_id
            )
        )
