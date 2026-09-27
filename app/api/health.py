from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_health_probe, get_settings
from app.api.schemas.errors import ErrorResponse
from app.api.schemas.health import HealthResponse
from app.core.config import Settings
from app.services.health import HealthProbe, ensure_ready

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    return HealthResponse()


@router.get(
    "/ready", response_model=HealthResponse, responses={503: {"model": ErrorResponse}}
)
async def ready(
    probe: Annotated[HealthProbe, Depends(get_health_probe)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    await ensure_ready(probe, settings.dependency_timeout_seconds)
    return HealthResponse()
