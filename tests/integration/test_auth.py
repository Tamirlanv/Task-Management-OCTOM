import asyncio

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

ACCOUNT = {
    "email": "alice@example.com",
    "name": "Alice",
    "password": "long-safe-password",
}


async def register_and_login(client: AsyncClient) -> dict[str, str]:
    response = await client.post("/api/v1/auth/register", json=ACCOUNT)
    assert response.status_code == 201, response.text
    login = await client.post("/api/v1/auth/login", json=ACCOUNT | {"name": "Alice"})
    assert login.status_code == 422
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": ACCOUNT["email"], "password": ACCOUNT["password"]},
    )
    assert login.status_code == 200, login.text
    result: dict[str, str] = login.json()
    return result


async def test_register_login_profile_and_duplicate(client: AsyncClient) -> None:
    pair = await register_and_login(client)
    headers = {"Authorization": f"Bearer {pair['access_token']}"}
    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["name"] == "Alice"
    assert "password" not in me.text
    renamed = await client.patch(
        "/api/v1/users/me", headers=headers, json={"name": "New"}
    )
    assert renamed.json()["name"] == "New"
    duplicate = await client.post(
        "/api/v1/auth/register", json=ACCOUNT | {"email": " ALICE@example.com "}
    )
    assert duplicate.status_code == 409
    assert (await client.get("/api/v1/users/me")).status_code == 401


async def test_refresh_replay_revokes_the_rotated_family(client: AsyncClient) -> None:
    original = await register_and_login(client)
    rotated = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]}
    )
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != original["refresh_token"]
    replay = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]}
    )
    assert replay.status_code == 401
    revoked = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}
    )
    assert revoked.status_code == 401


async def test_concurrent_refresh_has_one_winner_and_revokes_family(
    client: AsyncClient,
) -> None:
    pair = await register_and_login(client)
    responses = await asyncio.gather(
        *[
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
            )
            for _ in range(2)
        ]
    )
    assert sorted(response.status_code for response in responses) == [200, 401]
    winner = next(response for response in responses if response.status_code == 200)
    assert (
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": winner.json()["refresh_token"]},
        )
    ).status_code == 401


async def test_logout_and_logout_all(client: AsyncClient) -> None:
    first = await register_and_login(client)
    second = (
        await client.post(
            "/api/v1/auth/login",
            json={"email": ACCOUNT["email"], "password": ACCOUNT["password"]},
        )
    ).json()
    assert (
        await client.post(
            "/api/v1/auth/logout", json={"refresh_token": first["refresh_token"]}
        )
    ).status_code == 204
    assert (
        await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        )
    ).status_code == 401
    headers = {"Authorization": f"Bearer {second['access_token']}"}
    assert (
        await client.post("/api/v1/auth/logout-all", headers=headers)
    ).status_code == 204
    assert (
        await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
        )
    ).status_code == 401


async def test_invalid_credentials_and_refresh(client: AsyncClient) -> None:
    await register_and_login(client)
    for email in (ACCOUNT["email"], "unknown@example.com"):
        response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong"}
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthenticated"
    invalid = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "x" * 64}
    )
    assert invalid.status_code == 401


async def test_real_readiness(client: AsyncClient) -> None:
    assert (await client.get("/health/ready")).status_code == 200
