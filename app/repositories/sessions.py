from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import RefreshToken, SessionFamily


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_family(self, user_id: UUID, expires_at: datetime) -> SessionFamily:
        family = SessionFamily(user_id=user_id, expires_at=expires_at)
        self.session.add(family)
        await self.session.flush()
        return family

    async def add_token(self, family: SessionFamily, token_hash: str) -> None:
        self.session.add(
            RefreshToken(
                family_id=family.id, token_hash=token_hash, expires_at=family.expires_at
            )
        )
        await self.session.flush()

    async def lock_token(
        self, token_hash: str
    ) -> tuple[SessionFamily, RefreshToken] | None:
        family_id = await self.session.scalar(
            select(RefreshToken.family_id).where(RefreshToken.token_hash == token_hash)
        )
        if family_id is None:
            return None
        # All refresh/logout flows lock family before token; never the reverse.
        family = await self.session.scalar(
            select(SessionFamily).where(SessionFamily.id == family_id).with_for_update()
        )
        token = await self.session.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )
        return (family, token) if family is not None and token is not None else None

    async def revoke_all(self, user_id: UUID, now: datetime) -> None:
        await self.session.execute(
            update(SessionFamily)
            .where(SessionFamily.user_id == user_id)
            .values(revoked_at=now)
        )
