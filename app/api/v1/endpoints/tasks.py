from dataclasses import replace
from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import CurrentUser
from app.api.schemas.common import Page
from app.api.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate
from app.api.task_dependencies import Filters, Tasks
from app.services.errors import InvalidInput

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["tasks"])


@router.post(
    "/projects/{project_id}/tasks", status_code=201, response_model=TaskResponse
)
async def create(
    workspace_id: UUID,
    project_id: UUID,
    body: TaskCreate,
    user: CurrentUser,
    service: Tasks,
) -> TaskResponse:
    return TaskResponse.from_bundle(
        await service.create(workspace_id, project_id, user, body.command())
    )


@router.get("/tasks", response_model=Page[TaskResponse])
async def listing(
    workspace_id: UUID, user: CurrentUser, service: Tasks, filters: Filters
) -> Page[TaskResponse]:
    items, total = await service.list(workspace_id, user, filters.command())
    return Page(
        items=[TaskResponse.from_bundle(item) for item in items],
        total=total,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.get("/projects/{project_id}/tasks", response_model=Page[TaskResponse])
async def project_tasks(
    workspace_id: UUID,
    project_id: UUID,
    user: CurrentUser,
    service: Tasks,
    filters: Filters,
) -> Page[TaskResponse]:
    if filters.project_id is not None and filters.project_id != project_id:
        raise InvalidInput
    items, total = await service.list(
        workspace_id, user, replace(filters.command(), project_id=project_id)
    )
    return Page(
        items=[TaskResponse.from_bundle(item) for item in items],
        total=total,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get(
    workspace_id: UUID, task_id: UUID, user: CurrentUser, service: Tasks
) -> TaskResponse:
    return TaskResponse.from_bundle(await service.get(workspace_id, task_id, user))


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update(
    workspace_id: UUID,
    task_id: UUID,
    body: TaskUpdate,
    user: CurrentUser,
    service: Tasks,
) -> TaskResponse:
    return TaskResponse.from_bundle(
        await service.update(workspace_id, task_id, user, body.command())
    )


@router.delete("/tasks/{task_id}", status_code=204)
async def remove(
    workspace_id: UUID, task_id: UUID, user: CurrentUser, service: Tasks
) -> Response:
    await service.remove(workspace_id, task_id, user)
    return Response(status_code=204)
