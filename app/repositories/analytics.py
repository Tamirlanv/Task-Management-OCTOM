from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Task
from app.services.overview_contracts import CreationDay, Overview


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def overview(self, workspace_id: UUID, now: datetime) -> Overview:
        counts = (
            await self.session.execute(
                select(
                    func.count(),
                    func.count().filter(Task.status == "done"),
                    func.count().filter(Task.status == "in_progress"),
                    func.count().filter(
                        Task.due_at < now,
                        Task.status.not_in(("done", "cancelled")),
                    ),
                ).where(Task.workspace_id == workspace_id)
            )
        ).one()
        projects = await self.session.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.workspace_id == workspace_id)
        )
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=13
        )
        day = func.date(func.timezone("UTC", Task.created_at))
        rows = await self.session.execute(
            select(day, func.count())
            .where(
                Task.workspace_id == workspace_id,
                Task.created_at >= start,
                Task.created_at <= now,
            )
            .group_by(day)
        )
        daily = dict(rows.tuples().all())
        days = [start.date() + timedelta(days=index) for index in range(14)]
        return Overview(
            int(counts[0]),
            int(counts[1]),
            int(counts[2]),
            int(counts[3]),
            int(projects or 0),
            [CreationDay(day, int(daily.get(day, 0))) for day in days],
        )
