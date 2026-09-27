from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.integration.helpers import account, member, workspace

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("role", ["Admin", "Manager", "Member", "Viewer"])
async def test_catalog_permissions(client: AsyncClient, role: str) -> None:
    owner = await account(client, "owner")
    target = await account(client, "target")
    workspace_id = await workspace(client, owner)
    await member(client, workspace_id, owner, target, role)
    base = f"/api/v1/workspaces/{workspace_id}"
    for resource in ("projects", "tags"):
        path = f"{base}/{resource}"
        created = await client.post(
            path, headers=owner.headers, json={"name": "Initial"}
        )
        assert created.status_code == 201, created.text
        identifier = created.json()["id"]
        listing = await client.get(path, headers=target.headers)
        assert listing.status_code == 200
        assert listing.json()["total"] == 1
        allowed = role in ("Admin", "Manager")
        update = await client.patch(
            f"{path}/{identifier}", headers=target.headers, json={"name": "Changed"}
        )
        assert update.status_code == (200 if allowed else 403), update.text
        new = await client.post(path, headers=target.headers, json={"name": "Other"})
        assert new.status_code == (201 if allowed else 403), new.text
        removed = await client.delete(f"{path}/{identifier}", headers=target.headers)
        assert removed.status_code == (204 if allowed else 403), removed.text


async def test_catalog_validation_and_foreign_ids(client: AsyncClient) -> None:
    owner = await account(client, "owner")
    first = await workspace(client, owner)
    second = await workspace(client, owner)
    base = f"/api/v1/workspaces/{first}"
    for resource in ("projects", "tags"):
        response = await client.post(
            f"{base}/{resource}", headers=owner.headers, json={"name": "Unique"}
        )
        identifier = response.json()["id"]
        foreign = f"/api/v1/workspaces/{second}/{resource}/{identifier}"
        assert (
            await client.patch(foreign, headers=owner.headers, json={"name": "Changed"})
        ).status_code == 404
        assert (await client.delete(foreign, headers=owner.headers)).status_code == 404
        assert (
            await client.delete(f"{base}/{resource}/{uuid4()}", headers=owner.headers)
        ).status_code == 404
    project = (await client.get(f"{base}/projects", headers=owner.headers)).json()[
        "items"
    ][0]
    assert (
        await client.get(f"{base}/projects/{project['id']}", headers=owner.headers)
    ).status_code == 200
    assert (
        await client.get(
            f"/api/v1/workspaces/{second}/projects/{project['id']}",
            headers=owner.headers,
        )
    ).status_code == 404
    updated = await client.patch(
        f"{base}/projects/{project['id']}",
        headers=owner.headers,
        json={"description": "Details"},
    )
    assert updated.json()["description"] == "Details"
    assert (
        await client.post(
            f"{base}/tags", headers=owner.headers, json={"name": "UNIQUE"}
        )
    ).status_code == 409
    assert (
        await client.post(
            f"{base}/tags",
            headers=owner.headers,
            json={"name": "Invalid", "color": "red"},
        )
    ).status_code == 422
    tag = (await client.get(f"{base}/tags", headers=owner.headers)).json()["items"][0]
    tag_path = f"{base}/tags/{tag['id']}"
    assert (
        await client.patch(tag_path, headers=owner.headers, json={"color": "#aaBB12"})
    ).json()["color"] == "#aaBB12"
    assert (
        await client.patch(tag_path, headers=owner.headers, json={"color": None})
    ).json()["color"] is None
