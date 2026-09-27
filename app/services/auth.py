from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from app.models.session import SessionFamily
from app.models.user import User
from app.repositories.protocols import UnitOfWork
from app.services.errors import Conflict, Unauthenticated


class Passwords(Protocol):
    async def hash(self, password: str) -> str: ...
    async def verify(self, encoded: str | None, password: str) -> bool: ...


class AccessTokens(Protocol):
    def access(self, user_id: UUID) -> str: ...


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(
        self,
        uow: UnitOfWork,
        passwords: Passwords,
        access: AccessTokens,
        refresh_factory: Callable[[], str],
        digest: Callable[[str], str],
        access_ttl: int,
        session_ttl: int,
    ) -> None:
        self.uow = uow
        self.passwords = passwords
        self.access = access
        self.refresh_factory = refresh_factory
        self.digest = digest
        self.access_ttl = access_ttl
        self.session_ttl = session_ttl

    async def register(self, email: str, name: str, password: str) -> User:
        encoded = await self.passwords.hash(password)
        async with self.uow:
            if await self.uow.users.by_email(email) is not None:
                raise Conflict
            user = await self.uow.users.create(email, name, encoded)
            await self.uow.commit()
            return user

    async def login(self, email: str, password: str) -> TokenPair:
        async with self.uow:
            user = await self.uow.users.by_email(email)
            valid = await self.passwords.verify(
                user.password_hash if user is not None else None, password
            )
            if not valid or user is None:
                raise Unauthenticated
            family = await self.uow.sessions.create_family(
                user.id, datetime.now(UTC) + timedelta(seconds=self.session_ttl)
            )
            result = await self._issue(family)
            await self.uow.commit()
            return result

    async def refresh(self, raw_token: str) -> TokenPair:
        async with self.uow:
            pair = await self.uow.sessions.lock_token(self.digest(raw_token))
            if pair is None:
                raise Unauthenticated
            family, token = pair
            now = datetime.now(UTC)
            if family.revoked_at or family.expires_at <= now or token.expires_at <= now:
                raise Unauthenticated
            if token.used_at is not None:
                family.revoked_at = now
                # Persist replay revocation before raising the authentication error.
                await self.uow.commit()
                raise Unauthenticated
            token.used_at = now
            result = await self._issue(family)
            await self.uow.commit()
            return result

    async def logout(self, raw_token: str) -> None:
        async with self.uow:
            pair = await self.uow.sessions.lock_token(self.digest(raw_token))
            if pair is not None:
                pair[0].revoked_at = datetime.now(UTC)
                await self.uow.commit()

    async def logout_all(self, user_id: UUID) -> None:
        async with self.uow:
            await self.uow.sessions.revoke_all(user_id, datetime.now(UTC))
            await self.uow.commit()

    async def _issue(self, family: SessionFamily) -> TokenPair:
        refresh = self.refresh_factory()
        await self.uow.sessions.add_token(family, self.digest(refresh))
        return TokenPair(self.access.access(family.user_id), refresh, self.access_ttl)
