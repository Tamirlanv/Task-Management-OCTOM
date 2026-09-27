import asyncio
from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.integration.helpers import account, workspace
from tests.integration.task_helpers import board

pytestmark = pytest.mark.integration


async def test_task_lifecycle_permissions_and_nullable_patch(
    client: AsyncClient,
) -> None:
    team = await board(client)
    created = await client.post(
        team.tasks,
        headers=team.member.headers,
        json={
            "title": "Write tests",
            "tag_ids": [team.tag_id],
            "assignee_id": team.owner.id,
            "due_at": "2026-01-01T12:00:00+05:00",
        },
    )
    assert created.status_code == 201, created.text
    task = created.json()
    path = f"{team.base}/tasks/{task['id']}"
    assert task["created_by"] == team.member.id
    assert task["tag_ids"] == [team.tag_id]
    assert (await client.get(path, headers=team.viewer.headers)).status_code == 200
    assert (
        await client.post(
            team.tasks, headers=team.viewer.headers, json={"title": "Denied"}
        )
    ).status_code == 403
    assert (
        await client.patch(path, headers=team.viewer.headers, json={"status": "done"})
    ).status_code == 403
    assert (await client.delete(path, headers=team.viewer.headers)).status_code == 403
    updated = await client.patch(
        path,
        headers=team.member.headers,
        json={
            "title": "Ready",
            "description": "Details",
            "status": "in_progress",
            "priority": "urgent",
            "due_at": None,
            "assignee_id": None,
            "tag_ids": [],
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["due_at"] is None
    assert updated.json()["assignee_id"] is None
    assert updated.json()["tag_ids"] == []
    assert updated.json()["priority"] == "urgent"
    assert (
        await client.patch(path, headers=team.member.headers, json={"status": "done"})
    ).status_code == 200
    assert (await client.delete(path, headers=team.member.headers)).status_code == 204
    assert (await client.get(path, headers=team.owner.headers)).status_code == 404


async def test_member_only_edits_authored_or_assigned_tasks(
    client: AsyncClient,
) -> None:
    team = await board(client)
    created = await client.post(
        team.tasks, headers=team.owner.headers, json={"title": "Private edit"}
    )
    path = f"{team.base}/tasks/{created.json()['id']}"
    assert (
        await client.patch(path, headers=team.member.headers, json={"status": "done"})
    ).status_code == 403
    assert (await client.delete(path, headers=team.member.headers)).status_code == 403
    assert (
        await client.patch(
            path, headers=team.owner.headers, json={"assignee_id": team.member.id}
        )
    ).status_code == 200
    assert (
        await client.patch(path, headers=team.member.headers, json={"status": "done"})
    ).status_code == 200
    assert (await client.delete(path, headers=team.member.headers)).status_code == 204


async def test_task_relations_validation_and_atomicity(client: AsyncClient) -> None:
    team = await board(client)
    foreign_workspace = await workspace(client, team.owner)
    foreign_tag = (
        await client.post(
            f"/api/v1/workspaces/{foreign_workspace}/tags",
            headers=team.owner.headers,
            json={"name": "Foreign"},
        )
    ).json()["id"]
    outsider = await account(client, "outsider")
    for data in (
        {"assignee_id": team.viewer.id},
        {"assignee_id": outsider.id},
        {"tag_ids": [foreign_tag]},
        {"tag_ids": [team.tag_id, team.tag_id]},
        {"tag_ids": [str(uuid4()) for _ in range(21)]},
        {"due_at": "2026-01-01T12:00:00"},
        {"title": None},
        {"created_by": outsider.id},
    ):
        response = await client.post(
            team.tasks, headers=team.owner.headers, json={"title": "Invalid"} | data
        )
        assert response.status_code == 422, response.text
    assert (await client.get(team.tasks, headers=team.owner.headers)).json()[
        "total"
    ] == 0
    created = await client.post(
        team.tasks,
        headers=team.owner.headers,
        json={"title": "Original", "tag_ids": [team.tag_id]},
    )
    task_id = created.json()["id"]
    path = f"{team.base}/tasks/{task_id}"
    failed = await client.patch(
        path,
        headers=team.owner.headers,
        json={"title": "Must rollback", "tag_ids": [foreign_tag]},
    )
    assert failed.status_code == 422
    assert (await client.get(path, headers=team.owner.headers)).json()[
        "title"
    ] == "Original"
    for data in ({"title": None}, {"tag_ids": None}, {"project_id": team.project_id}):
        assert (
            await client.patch(path, headers=team.owner.headers, json=data)
        ).status_code == 422
    for method in (client.get, client.delete):
        assert (
            await method(
                f"/api/v1/workspaces/{foreign_workspace}/tasks/{task_id}",
                headers=team.owner.headers,
            )
        ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/workspaces/{foreign_workspace}/projects/{team.project_id}/tasks",
            headers=team.owner.headers,
            json={"title": "Foreign"},
        )
    ).status_code == 404


@pytest.mark.parametrize("action", ["viewer", "remove"])
async def test_member_changes_clear_assignments(
    client: AsyncClient, action: str
) -> None:
    team = await board(client)
    created = await client.post(
        team.tasks,
        headers=team.owner.headers,
        json={"title": "Assigned", "assignee_id": team.member.id},
    )
    target = f"{team.base}/members/{team.member.id}"
    if action == "viewer":
        response = await client.patch(
            target, headers=team.owner.headers, json={"role": "Viewer"}
        )
        assert response.status_code == 200
    else:
        assert (
            await client.delete(target, headers=team.owner.headers)
        ).status_code == 204
    task = await client.get(
        f"{team.base}/tasks/{created.json()['id']}", headers=team.owner.headers
    )
    assert task.json()["assignee_id"] is None
    assert task.json()["created_by"] == team.owner.id


async def test_assignment_racing_member_removal(client: AsyncClient) -> None:
    team = await board(client)
    created = await client.post(
        team.tasks, headers=team.owner.headers, json={"title": "Race"}
    )
    path = f"{team.base}/tasks/{created.json()['id']}"
    assigned, removed = await asyncio.gather(
        client.patch(
            path, headers=team.owner.headers, json={"assignee_id": team.member.id}
        ),
        client.delete(
            f"{team.base}/members/{team.member.id}", headers=team.owner.headers
        ),
    )
    assert assigned.status_code in (200, 422)
    assert removed.status_code == 204
    assert (await client.get(path, headers=team.owner.headers)).json()[
        "assignee_id"
    ] is None


async def test_cascade_deletes(client: AsyncClient) -> None:
    team = await board(client)
    created = await client.post(
        team.tasks,
        headers=team.owner.headers,
        json={
            "title": "Cascade",
            "tag_ids": [team.tag_id],
            "assignee_id": team.member.id,
        },
    )
    path = f"{team.base}/tasks/{created.json()['id']}"
    assert (
        await client.delete(
            f"{team.base}/tags/{team.tag_id}", headers=team.owner.headers
        )
    ).status_code == 204
    assert (await client.get(path, headers=team.owner.headers)).json()["tag_ids"] == []
    assert (
        await client.delete(
            f"{team.base}/projects/{team.project_id}", headers=team.owner.headers
        )
    ).status_code == 204
    assert (await client.get(path, headers=team.owner.headers)).status_code == 404
    new_project = (
        await client.post(
            f"{team.base}/projects", headers=team.owner.headers, json={"name": "Again"}
        )
    ).json()["id"]
    assert (
        await client.post(
            f"{team.base}/projects/{new_project}/tasks",
            headers=team.owner.headers,
            json={"title": "Delete with workspace", "assignee_id": team.member.id},
        )
    ).status_code == 201
    assert (
        await client.delete(team.base, headers=team.owner.headers)
    ).status_code == 204
    assert (
        await client.get("/api/v1/users/me", headers=team.member.headers)
    ).status_code == 200
