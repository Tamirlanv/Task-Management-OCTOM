from uuid import UUID

from app.repositories.protocols import UnitOfWork
from app.services.access import workspace_access
from app.services.contracts import Membership, Role
from app.services.errors import Conflict, NotFound
from app.services.policies import preserve_last_admin, require_admin


class MemberService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def list(
        self, workspace_id: UUID, actor_id: UUID, limit: int, offset: int
    ) -> tuple[list[tuple[Membership, str]], int]:
        async with self.uow:
            await workspace_access(self.uow, workspace_id, actor_id)
            result = await self.uow.memberships.list(workspace_id, limit, offset)
            await self.uow.commit()
            return result

    async def add(
        self, workspace_id: UUID, actor_id: UUID, email: str, role: Role
    ) -> tuple[Membership, str]:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            require_admin(actor)
            user = await self.uow.users.by_email(email)
            if user is None:
                raise NotFound
            if await self.uow.memberships.get(workspace_id, user.id):
                raise Conflict
            await self.uow.memberships.add(workspace_id, user.id, role)
            await self.uow.commit()
            return Membership(workspace_id, user.id, role), user.name

    async def change(
        self, workspace_id: UUID, actor_id: UUID, user_id: UUID, role: Role | None
    ) -> None:
        async with self.uow:
            _, actor = await workspace_access(
                self.uow, workspace_id, actor_id, write=True
            )
            require_admin(actor)
            target = await self.uow.memberships.get(workspace_id, user_id)
            if target is None:
                raise NotFound
            preserve_last_admin(
                target.role, role, await self.uow.memberships.admin_count(workspace_id)
            )
            if role is None:
                await self.uow.memberships.remove(workspace_id, user_id)
            else:
                await self.uow.memberships.change_role(workspace_id, user_id, role)
            await self.uow.commit()
