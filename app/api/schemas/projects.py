from uuid import UUID

from app.api.schemas.workspaces import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)


class ProjectCreate(WorkspaceCreate):
    pass


class ProjectUpdate(WorkspaceUpdate):
    pass


class ProjectResponse(WorkspaceResponse):
    workspace_id: UUID
    created_by: UUID
