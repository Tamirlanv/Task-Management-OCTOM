from datetime import UTC, datetime
from uuid import UUID

from app.repositories.protocols import UnitOfWork
from app.services.access import workspace_access
from app.services.contracts import Role
from app.services.overview_contracts import Overview


class OverviewService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get(self, workspace_id: UUID, actor_id: UUID) -> tuple[Overview, Role]:
        async with self.uow:
            _, member = await workspace_access(self.uow, workspace_id, actor_id)
            result = await self.uow.analytics.overview(workspace_id, datetime.now(UTC))
            await self.uow.commit()
            return result, member.role
