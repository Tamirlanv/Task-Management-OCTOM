import asyncio
from typing import cast
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import insert, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models import Task, TaskTag
from tests.integration.helpers import workspace
from tests.integration.task_helpers import board

pytestmark = pytest.mark.integration


def verify_migrations(connection: Connection) -> None:
    configuration = Config("alembic.ini")
    configuration.attributes["connection"] = connection
    command.check(configuration)
    command.downgrade(configuration, "cb6d1164e4c7")
    command.upgrade(configuration, "head")
    command.check(configuration)


async def test_schema_matches_models_and_upgrade_path(api: FastAPI) -> None:
    engine = cast(AsyncEngine, api.state.engine)
    async with engine.begin() as connection:
        await connection.run_sync(verify_migrations)
        roles = (
            (await connection.execute(text("SELECT name FROM roles ORDER BY name")))
            .scalars()
            .all()
        )
        assert roles == ["Admin", "Manager", "Member", "Viewer"]


async def test_composite_foreign_keys_reject_cross_workspace_data(
    api: FastAPI, client: AsyncClient
) -> None:
    team = await board(client)
    foreign_workspace = await workspace(client, team.owner)
    foreign_tag = (
        await client.post(
            f"/api/v1/workspaces/{foreign_workspace}/tags",
            headers=team.owner.headers,
            json={"name": "Foreign"},
        )
    ).json()["id"]
    task = (
        await client.post(
            team.tasks, headers=team.owner.headers, json={"title": "Safe"}
        )
    ).json()["id"]
    engine = cast(AsyncEngine, api.state.engine)
    with pytest.raises(IntegrityError):
        async with engine.begin() as connection:
            await connection.execute(
                insert(TaskTag).values(
                    workspace_id=UUID(team.workspace_id),
                    task_id=UUID(task),
                    tag_id=UUID(foreign_tag),
                )
            )
    with pytest.raises(IntegrityError):
        async with engine.begin() as connection:
            await connection.execute(
                insert(Task).values(
                    id=uuid4(),
                    workspace_id=UUID(foreign_workspace),
                    project_id=UUID(team.project_id),
                    title="Cross tenant",
                    created_by=UUID(team.owner.id),
                )
            )
    with pytest.raises(IntegrityError):
        async with engine.begin() as connection:
            await connection.execute(
                insert(Task).values(
                    id=uuid4(),
                    workspace_id=UUID(team.workspace_id),
                    project_id=UUID(team.project_id),
                    title="Missing member",
                    created_by=UUID(team.owner.id),
                    assignee_id=uuid4(),
                )
            )


async def test_concurrent_registration_is_atomic(client: AsyncClient) -> None:
    body = {
        "name": "Concurrent",
        "email": "race@example.com",
        "password": "long-enough-password",
    }
    responses = await asyncio.gather(
        *(client.post("/api/v1/auth/register", json=body) for _ in range(2))
    )
    assert sorted(response.status_code for response in responses) == [201, 409]
