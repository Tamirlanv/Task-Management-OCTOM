import os
from collections.abc import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.main import create_app


def upgrade(connection: Connection) -> None:
    configuration = Config("alembic.ini")
    configuration.attributes["connection"] = connection
    command.upgrade(configuration, "head")


@pytest.fixture
async def database(settings: Settings) -> AsyncIterator[None]:
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 and start compose.test.yaml")
    url = str(settings.database_url)
    if not url.endswith("/taskman_test"):
        raise RuntimeError(
            "Integration tests require the isolated taskman_test database"
        )
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(upgrade)
            await connection.execute(
                text("TRUNCATE users, workspaces, session_families CASCADE")
            )
        yield
    finally:
        await engine.dispose()


@pytest.fixture
async def api(settings: Settings, database: None) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    async with LifespanManager(application):
        # Only the dedicated test Redis database is cleared; never the user's DB 0.
        await application.state.redis.flushdb()
        yield application


@pytest.fixture
async def client(api: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=api), base_url="http://test"
    ) as http:
        yield http
