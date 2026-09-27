from types import TracebackType
from typing import Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.analytics import AnalyticsRepository
from app.repositories.catalog_protocols import Projects, Tags
from app.repositories.memberships import MembershipRepository
from app.repositories.projects import ProjectRepository
from app.repositories.protocols import Sessions, Users
from app.repositories.sessions import SessionRepository
from app.repositories.tags import TagRepository
from app.repositories.task_protocols import Tasks
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.repositories.workspace_protocols import Memberships, Workspaces
from app.repositories.workspaces import WorkspaceRepository
from app.services.errors import Conflict
from app.services.overview_contracts import Analytics


class SqlUnitOfWork:
    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self.factory = factory

    async def __aenter__(self) -> Self:
        self.session = self.factory()
        self.users: Users = UserRepository(self.session)
        self.sessions: Sessions = SessionRepository(self.session)
        self.workspaces: Workspaces = WorkspaceRepository(self.session)
        self.memberships: Memberships = MembershipRepository(self.session)
        self.projects: Projects = ProjectRepository(self.session)
        self.tags: Tags = TagRepository(self.session)
        self.tasks: Tasks = TaskRepository(self.session)
        self.analytics: Analytics = AnalyticsRepository(self.session)
        return self

    async def commit(self) -> None:
        await self.session.commit()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await self.session.rollback()
        finally:
            await self.session.close()
        if isinstance(exc, IntegrityError):
            raise Conflict from exc
