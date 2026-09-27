from uuid import UUID

from fastapi import APIRouter, Response

from app.api.catalog_dependencies import Tags
from app.api.dependencies import CurrentUser
from app.api.schemas.common import Page
from app.api.schemas.tags import TagCreate, TagResponse, TagUpdate
from app.api.workspace_dependencies import Paging

router = APIRouter(prefix="/workspaces/{workspace_id}/tags", tags=["tags"])


@router.post("", status_code=201, response_model=TagResponse)
async def create(
    workspace_id: UUID, body: TagCreate, user: CurrentUser, service: Tags
) -> TagResponse:
    return TagResponse.model_validate(
        await service.create(workspace_id, user, body.name, body.color)
    )


@router.get("", response_model=Page[TagResponse])
async def listing(
    workspace_id: UUID, user: CurrentUser, service: Tags, paging: Paging
) -> Page[TagResponse]:
    items, total = await service.list(workspace_id, user, paging.limit, paging.offset)
    return Page(
        items=[TagResponse.model_validate(item) for item in items],
        total=total,
        **paging.model_dump(),
    )


@router.patch("/{tag_id}", response_model=TagResponse)
async def update(
    workspace_id: UUID, tag_id: UUID, body: TagUpdate, user: CurrentUser, service: Tags
) -> TagResponse:
    return TagResponse.model_validate(
        await service.update(
            workspace_id,
            user,
            tag_id,
            body.name,
            body.color,
            "color" in body.model_fields_set,
        )
    )


@router.delete("/{tag_id}", status_code=204)
async def remove(
    workspace_id: UUID, tag_id: UUID, user: CurrentUser, service: Tags
) -> Response:
    await service.remove(workspace_id, user, tag_id)
    return Response(status_code=204)
