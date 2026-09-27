from uuid import UUID

from app.models.workspace import Workspace
from app.repositories.protocols import UnitOfWork
from app.services.contracts import Membership
from app.services.errors import NotFound
from app.services.policies import require_membership


async def workspace_access(
    uow: UnitOfWork, workspace_id: UUID, actor_id: UUID, *, write: bool = False
) -> tuple[Workspace, Membership]:
    # Writes lock the workspace before reading roles. This serializes membership,
    # assignment and resource mutations, protecting last-admin and Viewer rules.
    workspace = await uow.workspaces.get(workspace_id, lock=write)
    if workspace is None:
        raise NotFound
    member = require_membership(
        await uow.memberships.get(workspace_id, actor_id), workspace_id, actor_id
    )
    return workspace, member
