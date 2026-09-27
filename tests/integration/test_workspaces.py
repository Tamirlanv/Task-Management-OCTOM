import asyncio
from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.integration.helpers import account, member, workspace

pytestmark = pytest.mark.integration


async def test_workspace_crud_and_isolation(client: AsyncClient) -> None:
    owner = await account(client, "owner")
    outsider = await account(client, "outsider")
    workspace_id = await workspace(client, owner)
    path = f"/api/v1/workspaces/{workspace_id}"
    assert (await client.get(path, headers=owner.headers)).status_code == 200
    assert (await client.get(path, headers=outsider.headers)).status_code == 404
    assert (await client.get("/api/v1/workspaces", headers=outsider.headers)).json()[
        "total"
    ] == 0
    listing = await client.get(
        "/api/v1/workspaces?limit=1&offset=0", headers=owner.headers
    )
    assert listing.json()["total"] == 1
    assert (
        await client.get("/api/v1/workspaces?limit=101", headers=owner.headers)
    ).status_code == 422
    updated = await client.patch(
        path, headers=owner.headers, json={"name": "Changed", "description": "Plan"}
    )
    assert updated.json()["name"] == "Changed"
    assert (
        await client.patch(path, headers=owner.headers, json={"name": None})
    ).status_code == 422
    assert (await client.delete(path, headers=owner.headers)).status_code == 204
    assert (await client.get(path, headers=owner.headers)).status_code == 404


@pytest.mark.parametrize("role", ["Manager", "Member", "Viewer"])
async def test_members_cannot_manage_workspace_or_members(
    client: AsyncClient, role: str
) -> None:
    owner = await account(client, "owner")
    target = await account(client, "target")
    workspace_id = await workspace(client, owner)
    await member(client, workspace_id, owner, target, role)
    path = f"/api/v1/workspaces/{workspace_id}"
    assert (await client.get(path, headers=target.headers)).status_code == 200
    listing = await client.get(f"{path}/members", headers=target.headers)
    assert listing.json()["total"] == 2
    assert "email" not in listing.text
    assert (
        await client.patch(path, headers=target.headers, json={"name": "Denied"})
    ).status_code == 403
    assert (await client.delete(path, headers=target.headers)).status_code == 403
    assert (
        await client.patch(
            f"{path}/members/{target.id}",
            headers=target.headers,
            json={"role": "Admin"},
        )
    ).status_code == 403
    duplicate = await client.post(
        f"{path}/members", headers=owner.headers, json={"email": target.email}
    )
    assert duplicate.status_code == 409
    assert (
        await client.delete(f"{path}/members/{target.id}", headers=owner.headers)
    ).status_code == 204
    assert (await client.get(path, headers=target.headers)).status_code == 404


async def test_last_admin_and_concurrent_demotions(client: AsyncClient) -> None:
    owner = await account(client, "owner")
    second = await account(client, "second")
    workspace_id = await workspace(client, owner)
    path = f"/api/v1/workspaces/{workspace_id}/members"
    assert (
        await client.delete(f"{path}/{owner.id}", headers=owner.headers)
    ).status_code == 409
    await member(client, workspace_id, owner, second, "Admin")
    results = await asyncio.gather(
        *[
            client.patch(
                f"{path}/{actor.id}", headers=actor.headers, json={"role": "Member"}
            )
            for actor in (owner, second)
        ]
    )
    assert sorted(response.status_code for response in results) == [200, 409]
    remaining = await client.get(path, headers=owner.headers)
    assert sum(item["role"] == "Admin" for item in remaining.json()["items"]) == 1


async def test_unknown_member_and_workspace(client: AsyncClient) -> None:
    owner = await account(client, "owner")
    workspace_id = await workspace(client, owner)
    path = f"/api/v1/workspaces/{workspace_id}/members"
    assert (
        await client.post(
            path, headers=owner.headers, json={"email": "missing@example.com"}
        )
    ).status_code == 404
    assert (
        await client.delete(f"{path}/{uuid4()}", headers=owner.headers)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/workspaces/{uuid4()}", headers=owner.headers)
    ).status_code == 404
