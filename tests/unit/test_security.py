from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from pydantic import PostgresDsn, ValidationError

from app.core.config import Settings
from app.core.security import (
    PasswordSecurity,
    TokenSecurity,
    new_refresh_token,
    token_digest,
)
from app.services.errors import Unauthenticated


async def test_password_hashing_and_wrong_password() -> None:
    security = PasswordSecurity()
    encoded = await security.hash("long-unicode-password-秘密")
    assert encoded.startswith("$argon2id$")
    assert await security.verify(encoded, "long-unicode-password-秘密")
    assert not await security.verify(encoded, "wrong")
    assert not await security.verify(None, "wrong")
    assert not await security.verify("invalid hash", "wrong")


def test_access_claims_and_tampering(settings: Settings) -> None:
    security = TokenSecurity(settings)
    user_id = uuid4()
    token = security.access(user_id)
    assert security.subject(token) == user_id
    with pytest.raises(Unauthenticated):
        security.subject(token + "tampered")
    with pytest.raises(Unauthenticated):
        security.subject("garbage")


@pytest.mark.parametrize(
    "change", ["expired", "issuer", "audience", "type", "missing", "subject"]
)
def test_invalid_jwt_claims(settings: Settings, change: str) -> None:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": str(uuid4()),
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "access",
    }
    match change:
        case "expired":
            claims["exp"] = now - timedelta(seconds=1)
        case "issuer":
            claims["iss"] = "other"
        case "audience":
            claims["aud"] = "other"
        case "type":
            claims["type"] = "refresh"
        case "missing":
            del claims["jti"]
        case "subject":
            claims["sub"] = "not-a-uuid"
    token = jwt.encode(
        claims, settings.jwt_secret.get_secret_value(), algorithm="HS256"
    )
    with pytest.raises(Unauthenticated):
        TokenSecurity(settings).subject(token)


def test_refresh_tokens_are_random_and_hash_only() -> None:
    first, second = new_refresh_token(), new_refresh_token()
    assert len(first) == 64
    assert first != second
    assert token_digest(first) != first
    assert token_digest(first) == token_digest(first)


def test_settings_reject_unsafe_configuration(settings: Settings) -> None:
    valid = settings.model_dump()
    for changes in (
        {"jwt_secret": "short"},
        {"cors_origins": ["*"]},
        {"app_env": "production", "cors_origins": ["http://example.com"]},
        {"database_url": PostgresDsn("postgresql://user:pass@localhost/db")},
    ):
        with pytest.raises(ValidationError):
            Settings.model_validate(valid | changes)
