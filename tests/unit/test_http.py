from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from app.api.dependencies import get_health_probe
from app.core.config import Settings
from app.main import create_app
from app.services.errors import LastAdminConflict, PermissionDenied, Unauthenticated
from tests.unit.test_health import Probe


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    application = create_app(settings)
    application.dependency_overrides[get_health_probe] = lambda: Probe()
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as http_client:
            yield http_client


async def test_health_and_request_ids(client: AsyncClient) -> None:
    for path in ("/health/live", "/health/ready"):
        response = await client.get(path, headers={"X-Request-ID": "untrusted"})
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["X-Request-ID"] != "untrusted"


async def test_not_found_uses_error_contract(client: AsyncClient) -> None:
    response = await client.get("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


async def test_dependency_failure_is_opaque(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_health_probe] = lambda: Probe("database")
    response = await client.get("/health/ready")
    assert response.status_code == 503
    assert "credentials" not in response.text


async def test_cors_allowlist(client: AsyncClient) -> None:
    good = await client.get("/health/live", headers={"Origin": "http://localhost:5173"})
    assert good.headers["access-control-allow-origin"] == "http://localhost:5173"
    bad = await client.get("/health/live", headers={"Origin": "https://unknown.test"})
    assert "access-control-allow-origin" not in bad.headers


@pytest.mark.parametrize(
    ("error", "status"),
    [(LastAdminConflict(), 409), (PermissionDenied(), 403), (Unauthenticated(), 401)],
)
async def test_application_errors(
    app: FastAPI, client: AsyncClient, error: Exception, status: int
) -> None:
    @app.get("/failure")
    async def failure() -> None:
        raise error

    response = await client.get("/failure")
    assert response.status_code == status
    if status == 401:
        assert response.headers["www-authenticate"] == "Bearer"


class SecretInput(BaseModel):
    password: str = Field(min_length=100)


async def test_validation_never_echoes_secrets(
    app: FastAPI, client: AsyncClient
) -> None:
    @app.post("/validate")
    async def validate(body: SecretInput) -> None:
        return None

    response = await client.post("/validate", json={"password": "private-password"})
    assert response.status_code == 422
    assert "private-password" not in response.text


async def test_internal_errors_are_sanitized(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/broken")
    async def broken() -> None:
        raise RuntimeError("private-password")

    response = await client.get("/broken")
    assert response.status_code == 500
    assert "private-password" not in response.text
    assert response.headers["X-Request-ID"] == response.json()["request_id"]


async def test_openapi_exposes_health_contract(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    assert "503" in response.json()["paths"]["/health/ready"]["get"]["responses"]
    schemas = response.json()["components"]["schemas"]
    assert schemas["RegisterInput"]["examples"][0]["email"] == "alice@example.com"
    assert schemas["TaskCreate"]["examples"][0]["priority"] == "high"


async def test_metrics_endpoint(client: AsyncClient) -> None:
    await client.get("/health/live")
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "taskman_http_requests_total" in response.text
    assert "/health/live" in response.text
