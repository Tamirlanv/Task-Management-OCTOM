import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import Settings
from app.services.errors import Unauthenticated


class PasswordSecurity:
    def __init__(self) -> None:
        self.hasher = PasswordHasher()
        self.capacity = asyncio.Semaphore(4)
        self._dummy_hash: str | None = None

    async def hash(self, password: str) -> str:
        async with self.capacity:
            return await asyncio.to_thread(self.hasher.hash, password)

    async def verify(self, encoded: str | None, password: str) -> bool:
        if encoded is None:
            if self._dummy_hash is None:
                self._dummy_hash = await self.hash(secrets.token_urlsafe(32))
            encoded = self._dummy_hash
        async with self.capacity:
            return await asyncio.to_thread(self._verify, encoded, password)

    def _verify(self, encoded: str, password: str) -> bool:
        try:
            return self.hasher.verify(encoded, password)
        except (VerificationError, InvalidHashError):
            return False


class TokenSecurity:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def access(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(user_id),
                "jti": str(uuid4()),
                "iat": now,
                "exp": now + timedelta(seconds=self.settings.access_token_ttl_seconds),
                "iss": self.settings.jwt_issuer,
                "aud": self.settings.jwt_audience,
                "type": "access",
            },
            self.settings.jwt_secret.get_secret_value(),
            algorithm=self.settings.jwt_algorithm,
        )

    def subject(self, token: str) -> UUID:
        try:
            claims = jwt.decode(
                token,
                self.settings.jwt_secret.get_secret_value(),
                algorithms=[self.settings.jwt_algorithm],
                issuer=self.settings.jwt_issuer,
                audience=self.settings.jwt_audience,
                options={"require": ["sub", "jti", "iat", "exp", "iss", "aud", "type"]},
            )
            if claims["type"] != "access":
                raise Unauthenticated
            UUID(claims["jti"])
            return UUID(claims["sub"])
        except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError) as exc:
            raise Unauthenticated from exc


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
