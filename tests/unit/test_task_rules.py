from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.services.contracts import Priority, TaskStatus
from app.services.errors import InvalidInput
from app.services.task_rules import (
    as_utc,
    escape_search_term,
    is_overdue,
    validate_tag_ids,
    validate_task_filters,
)

NOW = datetime(2026, 9, 27, tzinfo=UTC)


@pytest.mark.parametrize("status", list(TaskStatus))
def test_overdue_status_and_deadline(status: TaskStatus) -> None:
    assert is_overdue(NOW - timedelta(seconds=1), status, now=NOW) == (
        status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)
    )
    assert not is_overdue(NOW, status, now=NOW)
    assert not is_overdue(NOW + timedelta(seconds=1), status, now=NOW)
    assert not is_overdue(None, status, now=NOW)


def test_timezone_normalization() -> None:
    assert as_utc(NOW.astimezone(timezone(timedelta(hours=5)))) == NOW
    with pytest.raises(InvalidInput):
        as_utc(datetime(2026, 9, 27))


def test_tag_limits_and_duplicates() -> None:
    validate_tag_ids(())
    validate_tag_ids(tuple(uuid4() for _ in range(20)))
    with pytest.raises(InvalidInput):
        validate_tag_ids(tuple(uuid4() for _ in range(21)))
    identifier = uuid4()
    with pytest.raises(InvalidInput):
        validate_tag_ids((identifier, identifier))


def test_search_is_literal() -> None:
    assert escape_search_term(r"50%_done\draft") == r"50\%\_done\\draft"
    assert escape_search_term("' OR 1=1") == "' OR 1=1"
    for invalid in ("", "a" * 201):
        with pytest.raises(InvalidInput):
            escape_search_term(invalid)


def test_filter_constraints() -> None:
    validate_task_filters(due_from=NOW, due_to=NOW)
    validate_task_filters(unassigned=True)
    validate_task_filters(assignee_id=uuid4())
    with pytest.raises(InvalidInput):
        validate_task_filters(unassigned=True, assignee_id=uuid4())
    with pytest.raises(InvalidInput):
        validate_task_filters(due_from=NOW + timedelta(seconds=1), due_to=NOW)
    with pytest.raises(InvalidInput):
        validate_task_filters(due_from=datetime(2026, 9, 27))


def test_priority_order_is_semantic() -> None:
    assert [priority.rank for priority in Priority] == [0, 1, 2, 3]
