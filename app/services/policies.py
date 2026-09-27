"""RBAC policies; membership data must be read inside the current transaction."""

from uuid import UUID

from app.services.contracts import Membership, Role, TaskOwnership
from app.services.errors import (
    InvalidAssignment,
    LastAdminConflict,
    NotFound,
    PermissionDenied,
)


def require_membership(
    membership: Membership | None, workspace_id: UUID, actor_id: UUID
) -> Membership:
    if (
        membership is None
        or membership.workspace_id != workspace_id
        or membership.user_id != actor_id
    ):
        raise NotFound
    return membership


def require_admin(membership: Membership) -> None:
    if membership.role != Role.ADMIN:
        raise PermissionDenied


def require_project_management(membership: Membership) -> None:
    if membership.role not in (Role.ADMIN, Role.MANAGER):
        raise PermissionDenied


def require_task_creation(membership: Membership) -> None:
    if membership.role == Role.VIEWER:
        raise PermissionDenied


def require_task_edit(membership: Membership, task: TaskOwnership) -> None:
    if membership.workspace_id != task.workspace_id:
        raise NotFound
    if membership.role in (Role.ADMIN, Role.MANAGER):
        return
    if membership.role == Role.MEMBER and membership.user_id in (
        task.created_by,
        task.assignee_id,
    ):
        return
    raise PermissionDenied


def require_assignable(
    membership: Membership | None, workspace_id: UUID, assignee_id: UUID
) -> None:
    if (
        membership is None
        or membership.workspace_id != workspace_id
        or membership.user_id != assignee_id
        or membership.role == Role.VIEWER
    ):
        raise InvalidAssignment


def preserve_last_admin(
    current_role: Role, next_role: Role | None, admin_count: int
) -> None:
    """Call under the workspace row lock, including when deleting membership."""
    if admin_count < 1:
        raise LastAdminConflict
    if current_role == Role.ADMIN and next_role != Role.ADMIN and admin_count == 1:
        raise LastAdminConflict
