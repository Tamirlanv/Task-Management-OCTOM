from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.integration.task_helpers import board

pytestmark = pytest.mark.integration


async def test_task_filters_search_sort_and_pagination(client: AsyncClient) -> None:
    team = await board(client)
    headers = team.owner.headers
    second_tag = (
        await client.post(f"{team.base}/tags", headers=headers, json={"name": "Second"})
    ).json()["id"]
    data = [
        {
            "title": "100%_ready",
            "status": "todo",
            "priority": "urgent",
            "due_at": "2020-01-01T00:00:00Z",
            "tag_ids": [team.tag_id, second_tag],
            "assignee_id": team.member.id,
        },
        {
            "title": "100xxready",
            "status": "done",
            "priority": "low",
            "due_at": "2020-01-01T00:00:00Z",
            "tag_ids": [team.tag_id],
        },
        {
            "title": "Future",
            "description": "search phrase",
            "status": "in_progress",
            "priority": "high",
        },
    ]
    for item in data:
        response = await client.post(team.tasks, headers=headers, json=item)
        assert response.status_code == 201, response.text
    path = f"{team.base}/tasks"
    for query, count in (
        ("q=100%25_ready", 1),
        ("q=SEARCH%20PHRASE", 1),
        ("overdue=true", 1),
        ("overdue=false", 2),
        ("unassigned=true", 2),
        (f"assignee_id={team.member.id}", 1),
        (f"created_by={team.owner.id}", 3),
        ("statuses=todo&statuses=done&priorities=urgent", 1),
        (f"tag_ids={team.tag_id}&tag_ids={second_tag}", 1),
        ("due_from=2019-01-01T00:00:00Z&due_to=2021-01-01T00:00:00Z", 2),
        (f"project_id={team.project_id}", 3),
        ("q=absent", 0),
    ):
        response = await client.get(f"{path}?{query}", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["total"] == count, (query, response.text)
    ordered = await client.get(
        f"{path}?sort=priority&direction=asc&limit=2", headers=headers
    )
    assert ordered.json()["total"] == 3
    assert [item["priority"] for item in ordered.json()["items"]] == ["low", "high"]
    last = await client.get(
        f"{path}?sort=priority&direction=asc&offset=2", headers=headers
    )
    assert last.json()["items"][0]["priority"] == "urgent"
    deadlines = await client.get(f"{path}?sort=due_at&direction=desc", headers=headers)
    assert deadlines.json()["items"][-1]["due_at"] is None
    for query in (
        "sort=untrusted",
        "limit=0",
        "offset=-1",
        "unexpected=1",
        "q=",
        f"unassigned=true&assignee_id={team.member.id}",
        "due_from=2030-01-01T00:00:00Z&due_to=2020-01-01T00:00:00Z",
    ):
        assert (
            await client.get(f"{path}?{query}", headers=headers)
        ).status_code == 422, query
    assert (
        await client.get(f"{team.tasks}?project_id={uuid4()}", headers=headers)
    ).status_code == 422
    assert (
        await client.get(f"{path}?project_id={uuid4()}", headers=headers)
    ).status_code == 404
