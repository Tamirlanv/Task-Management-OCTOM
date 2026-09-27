from fastapi import APIRouter, Depends

from app.api.rate_limit import enforce_api_limit
from app.api.schemas.errors import ErrorResponse
from app.api.v1.endpoints import (
    auth,
    members,
    overview,
    projects,
    tags,
    tasks,
    users,
    workspaces,
)

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(enforce_api_limit)],
    responses={
        status: {"model": ErrorResponse}
        for status in (401, 403, 404, 409, 422, 429, 503)
    },
)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(workspaces.router)
router.include_router(members.router)
router.include_router(projects.router)
router.include_router(tags.router)
router.include_router(tasks.router)
router.include_router(overview.router)
