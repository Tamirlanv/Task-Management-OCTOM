from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import CurrentUser
from app.api.schemas.common import Page
from app.api.schemas.workspaces import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.api.workspace_dependencies import Paging, Workspaces

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", status_code=201, response_model=WorkspaceResponse)
async def create(
    body: WorkspaceCreate, user: CurrentUser, service: Workspaces
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        await service.create(user, body.name, body.description)
    )


@router.get("", response_model=Page[WorkspaceResponse])
async def listing(
    user: CurrentUser, service: Workspaces, paging: Paging
) -> Page[WorkspaceResponse]:
    items, total = await service.list(user, paging.limit, paging.offset)
    return Page(
        items=[WorkspaceResponse.model_validate(item) for item in items],
        total=total,
        **paging.model_dump(),
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get(
    workspace_id: UUID, user: CurrentUser, service: Workspaces
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(await service.get(workspace_id, user))


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update(
    workspace_id: UUID, body: WorkspaceUpdate, user: CurrentUser, service: Workspaces
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        await service.update(workspace_id, user, body.name, body.description)
    )


@router.delete("/{workspace_id}", status_code=204)
async def remove(
    workspace_id: UUID, user: CurrentUser, service: Workspaces
) -> Response:
    await service.remove(workspace_id, user)
    return Response(status_code=204)
