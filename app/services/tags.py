from uuid import UUID

from app.models import Tag
from app.repositories.protocols import UnitOfWork
from app.services.access import workspace_access
from app.services.errors import NotFound
from app.services.policies import require_project_management


class TagService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create(
        self, workspace_id: UUID, actor_id: UUID, name: str, color: str | None
    ) -> Tag:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            require_project_management(actor)
            tag = await self.uow.tags.create(workspace_id, name, color)
            await self.uow.commit()
            return tag

    async def list(
        self, workspace_id: UUID, actor_id: UUID, limit: int, offset: int
    ) -> tuple[list[Tag], int]:
        async with self.uow:
            await workspace_access(self.uow, workspace_id, actor_id)
            result = await self.uow.tags.list(workspace_id, limit, offset)
            await self.uow.commit()
            return result

    async def update(
        self,
        workspace_id: UUID,
        actor_id: UUID,
        tag_id: UUID,
        name: str | None,
        color: str | None,
        replace_color: bool,
    ) -> Tag:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            tag = await self.uow.tags.get(workspace_id, tag_id)
            if tag is None:
                raise NotFound
            require_project_management(actor)
            if name is not None:
                tag.name = name
            if replace_color:
                tag.color = color
            await self.uow.tags.save(tag)
            await self.uow.commit()
            return tag

    async def remove(self, workspace_id: UUID, actor_id: UUID, tag_id: UUID) -> None:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            if await self.uow.tags.get(workspace_id, tag_id) is None:
                raise NotFound
            require_project_management(actor)
            await self.uow.tags.remove(workspace_id, tag_id)
            await self.uow.commit()
