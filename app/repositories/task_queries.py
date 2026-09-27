from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, and_, case, or_, select

from app.models import Task, TaskTag
from app.services.contracts import Priority
from app.services.task_contracts import TaskQuery
from app.services.task_rules import escape_search_term


def filtered_tasks(workspace_id: UUID, filters: TaskQuery) -> Select[tuple[Task]]:
    query = select(Task).where(Task.workspace_id == workspace_id)
    for column, value in (
        (Task.project_id, filters.project_id),
        (Task.assignee_id, filters.assignee_id),
        (Task.created_by, filters.created_by),
    ):
        if value is not None:
            query = query.where(column == value)
    if filters.statuses:
        query = query.where(Task.status.in_(filters.statuses))
    if filters.priorities:
        query = query.where(Task.priority.in_(filters.priorities))
    if filters.unassigned:
        query = query.where(Task.assignee_id.is_(None))
    if filters.due_from is not None:
        query = query.where(Task.due_at >= filters.due_from)
    if filters.due_to is not None:
        query = query.where(Task.due_at <= filters.due_to)
    if filters.overdue is not None:
        overdue = and_(
            Task.due_at.is_not(None),
            Task.due_at < datetime.now(UTC),
            Task.status.not_in(("done", "cancelled")),
        )
        query = query.where(overdue if filters.overdue else ~overdue)
    if filters.q is not None:
        term = f"%{escape_search_term(filters.q)}%"
        query = query.where(
            or_(
                Task.title.ilike(term, escape="\\"),
                Task.description.ilike(term, escape="\\"),
            )
        )
    for tag_id in filters.tag_ids:
        query = query.where(
            select(TaskTag.task_id)
            .where(
                TaskTag.workspace_id == workspace_id,
                TaskTag.task_id == Task.id,
                TaskTag.tag_id == tag_id,
            )
            .exists()
        )
    return query


def sorted_tasks(query: Select[tuple[Task]], filters: TaskQuery) -> Select[tuple[Task]]:
    columns = {
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
        "due_at": Task.due_at,
        "priority": case(
            {priority.value: priority.rank for priority in Priority},
            value=Task.priority,
        ),
    }
    column = columns[filters.sort]
    order = column.desc() if filters.direction == "desc" else column.asc()
    identifier = Task.id.desc() if filters.direction == "desc" else Task.id.asc()
    return (
        query.order_by(order.nulls_last(), identifier)
        .limit(filters.limit)
        .offset(filters.offset)
    )
