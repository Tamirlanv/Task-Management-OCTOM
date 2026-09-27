from uuid import UUID

from app.models.user import User
from app.repositories.protocols import UnitOfWork
from app.services.errors import Unauthenticated


class UserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get(self, user_id: UUID) -> User:
        async with self.uow:
            user = await self.uow.users.get(user_id)
            if user is None:
                raise Unauthenticated
            # End the read transaction without expiring this explicit result.
            await self.uow.commit()
            return user

    async def rename(self, user_id: UUID, name: str) -> User:
        async with self.uow:
            user = await self.uow.users.get(user_id)
            if user is None:
                raise Unauthenticated
            await self.uow.users.rename(user, name)
            await self.uow.commit()
            return user
