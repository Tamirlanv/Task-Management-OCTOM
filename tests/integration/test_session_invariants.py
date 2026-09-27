from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.security import TokenSecurity, token_digest
from app.models import RefreshToken, SessionFamily
from tests.integration.test_auth import register_and_login

pytestmark = pytest.mark.integration


async def test_rotation_keeps_absolute_expiry_and_stores_only_hashes(
    api: FastAPI, client: AsyncClient
) -> None:
    pair = await register_and_login(client)
    engine = cast(AsyncEngine, api.state.engine)
    async with engine.connect() as connection:
        original_expiry = await connection.scalar(select(SessionFamily.expires_at))
        stored = await connection.scalar(select(RefreshToken.token_hash))
        assert stored == token_digest(pair["refresh_token"])
        assert stored != pair["refresh_token"]
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
    )
    assert response.status_code == 200
    async with engine.connect() as connection:
        assert (
            await connection.scalar(select(SessionFamily.expires_at)) == original_expiry
        )
        expires = (
            (await connection.execute(select(RefreshToken.expires_at))).scalars().all()
        )
        assert len(expires) == 2
        assert all(value == original_expiry for value in expires)


@pytest.mark.parametrize("expire_family", [True, False])
async def test_expired_refresh_is_rejected(
    api: FastAPI, client: AsyncClient, expire_family: bool
) -> None:
    pair = await register_and_login(client)
    engine = cast(AsyncEngine, api.state.engine)
    model = SessionFamily if expire_family else RefreshToken
    async with engine.begin() as connection:
        await connection.execute(
            update(model).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
    )
    assert response.status_code == 401


async def test_token_for_missing_user_cannot_access_api(
    api: FastAPI, client: AsyncClient
) -> None:
    token = cast(TokenSecurity, api.state.tokens).access(uuid4())
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 401
    assert (
        await client.patch(
            "/api/v1/users/me", headers=headers, json={"name": "No user"}
        )
    ).status_code == 401
