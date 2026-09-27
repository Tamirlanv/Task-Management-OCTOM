from uuid import UUID

from fastapi import APIRouter, Response

from app.api.catalog_dependencies import Projects
from app.api.dependencies import CurrentUser
from app.api.schemas.common import Page
from app.api.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from app.api.workspace_dependencies import Paging

router = APIRouter(prefix="/workspaces/{workspace_id}/projects", tags=["projects"])


@router.post("", status_code=201, response_model=ProjectResponse)
async def create(
    workspace_id: UUID, body: ProjectCreate, user: CurrentUser, service: Projects
) -> ProjectResponse:
    return ProjectResponse.model_validate(
        await service.create(workspace_id, user, body.name, body.description)
    )


@router.get("", response_model=Page[ProjectResponse])
async def listing(
    workspace_id: UUID, user: CurrentUser, service: Projects, paging: Paging
) -> Page[ProjectResponse]:
    items, total = await service.list(workspace_id, user, paging.limit, paging.offset)
    return Page(
        items=[ProjectResponse.model_validate(item) for item in items],
        total=total,
        **paging.model_dump(),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get(
    workspace_id: UUID, project_id: UUID, user: CurrentUser, service: Projects
) -> ProjectResponse:
    return ProjectResponse.model_validate(
        await service.get(workspace_id, user, project_id)
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update(
    workspace_id: UUID,
    project_id: UUID,
    body: ProjectUpdate,
    user: CurrentUser,
    service: Projects,
) -> ProjectResponse:
    return ProjectResponse.model_validate(
        await service.update(
            workspace_id, user, project_id, body.name, body.description
        )
    )


@router.delete("/{project_id}", status_code=204)
async def remove(
    workspace_id: UUID, project_id: UUID, user: CurrentUser, service: Projects
) -> Response:
    await service.remove(workspace_id, user, project_id)
    return Response(status_code=204)
