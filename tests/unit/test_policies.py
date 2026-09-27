from uuid import uuid4

import pytest

from app.services.contracts import Membership, Role, TaskOwnership
from app.services.errors import (
    InvalidAssignment,
    LastAdminConflict,
    NotFound,
    PermissionDenied,
)
from app.services.policies import (
    preserve_last_admin,
    require_admin,
    require_assignable,
    require_membership,
    require_project_management,
    require_task_creation,
    require_task_edit,
)


@pytest.mark.parametrize("role", list(Role))
def test_role_permissions(role: Role) -> None:
    member = Membership(uuid4(), uuid4(), role)
    checks = [
        (require_admin, role == Role.ADMIN),
        (require_project_management, role in (Role.ADMIN, Role.MANAGER)),
        (require_task_creation, role != Role.VIEWER),
    ]
    for check, allowed in checks:
        if allowed:
            check(member)
        else:
            with pytest.raises(PermissionDenied):
                check(member)


@pytest.mark.parametrize("role", list(Role))
@pytest.mark.parametrize("relationship", ["author", "assignee", "unrelated"])
def test_task_edit_matrix(role: Role, relationship: str) -> None:
    member = Membership(uuid4(), uuid4(), role)
    task = TaskOwnership(
        member.workspace_id,
        member.user_id if relationship == "author" else uuid4(),
        member.user_id if relationship == "assignee" else None,
    )
    allowed = role in (Role.ADMIN, Role.MANAGER) or (
        role == Role.MEMBER and relationship != "unrelated"
    )
    if allowed:
        require_task_edit(member, task)
    else:
        with pytest.raises(PermissionDenied):
            require_task_edit(member, task)


@pytest.mark.parametrize("role", list(Role))
def test_cross_workspace_task_is_hidden(role: Role) -> None:
    member = Membership(uuid4(), uuid4(), role)
    with pytest.raises(NotFound):
        require_task_edit(member, TaskOwnership(uuid4(), member.user_id))


def test_membership_must_match_actor_and_workspace() -> None:
    member = Membership(uuid4(), uuid4(), Role.ADMIN)
    assert require_membership(member, member.workspace_id, member.user_id) == member
    for supplied, workspace, actor in [
        (None, member.workspace_id, member.user_id),
        (member, uuid4(), member.user_id),
        (member, member.workspace_id, uuid4()),
    ]:
        with pytest.raises(NotFound):
            require_membership(supplied, workspace, actor)


@pytest.mark.parametrize("role", list(Role))
def test_assignable_roles(role: Role) -> None:
    member = Membership(uuid4(), uuid4(), role)
    if role != Role.VIEWER:
        require_assignable(member, member.workspace_id, member.user_id)
    else:
        with pytest.raises(InvalidAssignment):
            require_assignable(member, member.workspace_id, member.user_id)


def test_assignment_rejects_missing_or_foreign_member() -> None:
    member = Membership(uuid4(), uuid4(), Role.MEMBER)
    for supplied, workspace, actor in [
        (None, member.workspace_id, member.user_id),
        (member, uuid4(), member.user_id),
        (member, member.workspace_id, uuid4()),
    ]:
        with pytest.raises(InvalidAssignment):
            require_assignable(supplied, workspace, actor)


@pytest.mark.parametrize("next_role", [None, *list(Role)])
def test_last_admin_cannot_leave_or_be_demoted(next_role: Role | None) -> None:
    if next_role == Role.ADMIN:
        preserve_last_admin(Role.ADMIN, next_role, 1)
    else:
        with pytest.raises(LastAdminConflict):
            preserve_last_admin(Role.ADMIN, next_role, 1)
    preserve_last_admin(Role.ADMIN, next_role, 2)
    preserve_last_admin(Role.MEMBER, next_role, 1)


def test_invalid_admin_count_fails_closed() -> None:
    with pytest.raises(LastAdminConflict):
        preserve_last_admin(Role.ADMIN, Role.ADMIN, 0)
