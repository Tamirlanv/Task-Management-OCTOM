from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def by_email(self, email: str) -> User | None:
        result = await self.session.scalars(select(User).where(User.email == email))
        return result.one_or_none()

    async def get(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def create(self, email: str, name: str, password_hash: str) -> User:
        user = User(email=email, name=name, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        return user

    async def rename(self, user: User, name: str) -> User:
        user.name = name
        await self.session.flush()
        await self.session.refresh(user)
        return user
