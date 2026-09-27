from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tag


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, workspace_id: UUID, tag_id: UUID) -> Tag | None:
        return (
            await self.session.scalars(
                select(Tag).where(Tag.workspace_id == workspace_id, Tag.id == tag_id)
            )
        ).one_or_none()

    async def count_ids(self, workspace_id: UUID, tag_ids: tuple[UUID, ...]) -> int:
        total = await self.session.scalar(
            select(func.count())
            .select_from(Tag)
            .where(Tag.workspace_id == workspace_id, Tag.id.in_(tag_ids))
        )
        return int(total or 0)

    async def list(
        self, workspace_id: UUID, limit: int, offset: int
    ) -> tuple[list[Tag], int]:
        query = select(Tag).where(Tag.workspace_id == workspace_id)
        total = await self.session.scalar(
            select(func.count()).select_from(query.subquery())
        )
        items = await self.session.scalars(
            query.order_by(Tag.name, Tag.id).limit(limit).offset(offset)
        )
        return list(items), int(total or 0)

    async def create(self, workspace_id: UUID, name: str, color: str | None) -> Tag:
        tag = Tag(workspace_id=workspace_id, name=name, color=color)
        self.session.add(tag)
        await self.session.flush()
        return tag

    async def save(self, tag: Tag) -> None:
        await self.session.flush()

    async def remove(self, workspace_id: UUID, tag_id: UUID) -> None:
        await self.session.execute(
            delete(Tag).where(Tag.workspace_id == workspace_id, Tag.id == tag_id)
        )
