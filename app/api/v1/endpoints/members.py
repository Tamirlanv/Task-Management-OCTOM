from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import CurrentUser
from app.api.schemas.common import Page
from app.api.schemas.workspaces import MemberCreate, MemberResponse, MemberUpdate
from app.api.workspace_dependencies import Members, Paging

router = APIRouter(prefix="/workspaces/{workspace_id}/members", tags=["members"])


@router.get("", response_model=Page[MemberResponse])
async def listing(
    workspace_id: UUID, user: CurrentUser, service: Members, paging: Paging
) -> Page[MemberResponse]:
    items, total = await service.list(workspace_id, user, paging.limit, paging.offset)
    return Page(
        items=[
            MemberResponse(user_id=member.user_id, name=name, role=member.role)
            for member, name in items
        ],
        total=total,
        **paging.model_dump(),
    )


@router.post("", status_code=201, response_model=MemberResponse)
async def add(
    workspace_id: UUID, body: MemberCreate, user: CurrentUser, service: Members
) -> MemberResponse:
    member, name = await service.add(workspace_id, user, str(body.email), body.role)
    return MemberResponse(user_id=member.user_id, name=name, role=member.role)


@router.patch("/{user_id}", response_model=MemberUpdate)
async def change(
    workspace_id: UUID,
    user_id: UUID,
    body: MemberUpdate,
    user: CurrentUser,
    service: Members,
) -> MemberUpdate:
    await service.change(workspace_id, user, user_id, body.role)
    return body


@router.delete("/{user_id}", status_code=204)
async def remove(
    workspace_id: UUID, user_id: UUID, user: CurrentUser, service: Members
) -> Response:
    await service.change(workspace_id, user, user_id, None)
    return Response(status_code=204)
