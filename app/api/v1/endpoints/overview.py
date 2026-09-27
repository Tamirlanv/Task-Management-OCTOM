from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, get_uow
from app.api.schemas.overview import OverviewResponse
from app.repositories.protocols import UnitOfWork
from app.services.overview import OverviewService

router = APIRouter(prefix="/workspaces", tags=["overview"])


@router.get("/{workspace_id}/overview", response_model=OverviewResponse)
async def get(
    workspace_id: UUID,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OverviewResponse:
    result, role = await OverviewService(uow).get(workspace_id, user)
    return OverviewResponse(role=role, statistics=result)
