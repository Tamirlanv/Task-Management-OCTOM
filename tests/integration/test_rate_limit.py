import asyncio

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from redis.asyncio import Redis

from app.core.rate_limit import RateLimiter
from app.services.errors import DependencyUnavailable, RateLimited

pytestmark = pytest.mark.integration


async def test_login_limit_and_retry_after(client: AsyncClient) -> None:
    for _ in range(5):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "absent@example.com", "password": "wrong"},
        )
        assert response.status_code == 401
    response = await client.post(
        "/api/v1/auth/login", json={"email": "absent@example.com", "password": "wrong"}
    )
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0
    assert response.json()["error"]["code"] == "rate_limited"


async def test_concurrent_rate_limit_is_atomic(api: FastAPI) -> None:
    limiter = RateLimiter(api.state.redis, "test-only")

    async def attempt() -> bool:
        try:
            await limiter.check("concurrent-subject", 3)
            return True
        except RateLimited:
            return False

    results = await asyncio.gather(*(attempt() for _ in range(10)))
    assert sum(results) == 3


async def test_redis_failure_fails_closed() -> None:
    redis = Redis(host="127.0.0.1", port=1, socket_connect_timeout=0.1)
    try:
        with pytest.raises(DependencyUnavailable):
            await RateLimiter(redis, "test-only").check("subject", 5)
    finally:
        await redis.aclose()


async def test_invalid_bearer_uses_auth_error(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/workspaces", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
