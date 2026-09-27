from datetime import UTC, datetime
from uuid import UUID

from app.services.contracts import TaskStatus
from app.services.errors import InvalidInput


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidInput
    return value.astimezone(UTC)


def is_overdue(due_at: datetime | None, status: TaskStatus, *, now: datetime) -> bool:
    instant = as_utc(now)
    if due_at is None:
        return False
    deadline = as_utc(due_at)
    return status not in (TaskStatus.DONE, TaskStatus.CANCELLED) and deadline < instant


def validate_tag_ids(tag_ids: tuple[UUID, ...]) -> None:
    if len(tag_ids) > 20 or len(set(tag_ids)) != len(tag_ids):
        raise InvalidInput


def escape_search_term(term: str) -> str:
    """Escape PostgreSQL LIKE metacharacters; SQL must still be parameterized."""
    if not 1 <= len(term) <= 200:
        raise InvalidInput
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def validate_task_filters(
    *,
    assignee_id: UUID | None = None,
    unassigned: bool = False,
    due_from: datetime | None = None,
    due_to: datetime | None = None,
) -> None:
    if unassigned and assignee_id is not None:
        raise InvalidInput
    start = as_utc(due_from) if due_from is not None else None
    end = as_utc(due_to) if due_to is not None else None
    if start is not None and end is not None and start > end:
        raise InvalidInput
