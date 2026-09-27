from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import update

from app.models import Task
from tests.integration.helpers import workspace
from tests.integration.task_helpers import board

pytestmark = pytest.mark.integration


async def test_overview_counts_tenant_access_and_empty_days(
    client: AsyncClient,
) -> None:
    team = await board(client)
    foreign = await workspace(client, team.owner, "Separate")
    path = f"{team.base}/overview"
    empty = await client.get(path, headers=team.viewer.headers)
    assert empty.status_code == 200
    assert empty.json()["role"] == "Viewer"
    stats = empty.json()["statistics"]
    assert stats["total"] == stats["done"] == stats["overdue"] == 0
    assert stats["projects"] == 1
    assert len(stats["days"]) == 14
    assert all(day["count"] == 0 for day in stats["days"])
    assert (await client.get(path)).status_code == 401
    assert (
        await client.get(
            f"/api/v1/workspaces/{foreign}/overview", headers=team.viewer.headers
        )
    ).status_code == 404

    for status in ("todo", "in_progress", "done", "cancelled"):
        response = await client.post(
            team.tasks,
            headers=team.owner.headers,
            json={
                "title": status,
                "status": status,
                "due_at": "2000-01-01T00:00:00Z",
            },
        )
        assert response.status_code == 201
    result = (await client.get(path, headers=team.owner.headers)).json()
    assert result["role"] == "Admin"
    assert result["statistics"] | {"days": []} == {
        "total": 4,
        "done": 1,
        "in_progress": 1,
        "overdue": 2,
        "projects": 1,
        "days": [],
    }
    assert sum(day["count"] for day in result["statistics"]["days"]) == 4
    other = (
        await client.get(
            f"/api/v1/workspaces/{foreign}/overview", headers=team.owner.headers
        )
    ).json()
    assert other["statistics"]["total"] == other["statistics"]["projects"] == 0


async def test_overview_uses_creation_dates_with_bounded_utc_window(
    client: AsyncClient,
    api: FastAPI,
) -> None:
    team = await board(client)
    now = datetime.now(UTC)
    for days in (0, 3, 13, 14, 90):
        response = await client.post(
            team.tasks, headers=team.owner.headers, json={"title": f"Day {days}"}
        )
        async with api.state.session_factory() as session:
            await session.execute(
                update(Task)
                .where(Task.id == response.json()["id"])
                .values(created_at=now - timedelta(days=days))
            )
            await session.commit()
    result = (
        await client.get(f"{team.base}/overview", headers=team.owner.headers)
    ).json()["statistics"]
    assert result["total"] == 5
    assert sum(day["count"] for day in result["days"]) == 3
    assert result["days"][-1]["date"] == now.date().isoformat()
