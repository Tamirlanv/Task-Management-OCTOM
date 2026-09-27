from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RoleModel, Task, User, WorkspaceMembership
from app.services.contracts import Membership, Role


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        role = await self.session.scalar(
            select(RoleModel.name)
            .join(WorkspaceMembership)
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
            )
        )
        return Membership(workspace_id, user_id, Role(role)) if role else None

    async def list(
        self, workspace_id: UUID, limit: int, offset: int
    ) -> tuple[list[tuple[Membership, str]], int]:
        query = (
            select(WorkspaceMembership.user_id, RoleModel.name, User.name)
            .join(RoleModel)
            .join(User)
            .where(WorkspaceMembership.workspace_id == workspace_id)
        )
        total = await self.session.scalar(
            select(func.count()).select_from(query.subquery())
        )
        rows = await self.session.execute(
            query.order_by(WorkspaceMembership.joined_at, WorkspaceMembership.user_id)
            .limit(limit)
            .offset(offset)
        )
        return [
            (Membership(workspace_id, user, Role(role)), name)
            for user, role, name in rows
        ], int(total or 0)

    async def add(self, workspace_id: UUID, user_id: UUID, role: Role) -> None:
        role_id = await self.session.scalar(
            select(RoleModel.id).where(RoleModel.name == role.value)
        )
        self.session.add(
            WorkspaceMembership(
                workspace_id=workspace_id, user_id=user_id, role_id=role_id
            )
        )
        await self.session.flush()

    async def admin_count(self, workspace_id: UUID) -> int:
        count = await self.session.scalar(
            select(func.count())
            .select_from(WorkspaceMembership)
            .join(RoleModel)
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                RoleModel.name == Role.ADMIN.value,
            )
        )
        return int(count or 0)

    async def change_role(self, workspace_id: UUID, user_id: UUID, role: Role) -> None:
        role_id = await self.session.scalar(
            select(RoleModel.id).where(RoleModel.name == role.value)
        )
        await self.session.execute(
            update(WorkspaceMembership)
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
            )
            .values(role_id=role_id)
        )
        if role == Role.VIEWER:
            await self._unassign(workspace_id, user_id)

    async def remove(self, workspace_id: UUID, user_id: UUID) -> None:
        await self._unassign(workspace_id, user_id)
        await self.session.execute(
            delete(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
            )
        )

    async def _unassign(self, workspace_id: UUID, user_id: UUID) -> None:
        await self.session.execute(
            update(Task)
            .where(Task.workspace_id == workspace_id, Task.assignee_id == user_id)
            .values(assignee_id=None)
        )
