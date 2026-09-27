from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.models.session import RefreshToken, SessionFamily
from app.models.user import User
from app.repositories.catalog_protocols import Projects, Tags
from app.repositories.task_protocols import Tasks
from app.repositories.workspace_protocols import Memberships, Workspaces
from app.services.overview_contracts import Analytics


class Users(Protocol):
    async def by_email(self, email: str) -> User | None: ...
    async def get(self, user_id: UUID) -> User | None: ...
    async def create(self, email: str, name: str, password_hash: str) -> User: ...
    async def rename(self, user: User, name: str) -> User: ...


class Sessions(Protocol):
    async def create_family(
        self, user_id: UUID, expires_at: datetime
    ) -> SessionFamily: ...
    async def add_token(self, family: SessionFamily, token_hash: str) -> None: ...
    async def lock_token(
        self, token_hash: str
    ) -> tuple[SessionFamily, RefreshToken] | None: ...
    async def revoke_all(self, user_id: UUID, now: datetime) -> None: ...


class UnitOfWork(Protocol):
    analytics: Analytics
    tasks: Tasks
    projects: Projects
    tags: Tags
    workspaces: Workspaces
    memberships: Memberships
    users: Users
    sessions: Sessions

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...
