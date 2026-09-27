from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.security import (
    PasswordSecurity,
    TokenSecurity,
    new_refresh_token,
    token_digest,
)
from app.repositories.protocols import UnitOfWork
from app.repositories.unit_of_work import SqlUnitOfWork
from app.services.auth import AuthService
from app.services.errors import Unauthenticated
from app.services.health import HealthProbe
from app.services.users import UserService


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_health_probe(request: Request) -> HealthProbe:
    return cast(HealthProbe, request.app.state.health_probe)


def get_uow(request: Request) -> UnitOfWork:
    factory = cast(async_sessionmaker[AsyncSession], request.app.state.session_factory)
    return SqlUnitOfWork(factory)


def get_auth_service(
    request: Request, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> AuthService:
    settings = get_settings(request)
    return AuthService(
        uow,
        cast(PasswordSecurity, request.app.state.passwords),
        cast(TokenSecurity, request.app.state.tokens),
        new_refresh_token,
        token_digest,
        settings.access_token_ttl_seconds,
        settings.refresh_session_ttl_seconds,
    )


def get_user_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> UserService:
    return UserService(uow)


bearer = HTTPBearer(auto_error=False)


async def current_user_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> UUID:
    if credentials is None:
        raise Unauthenticated
    tokens = cast(TokenSecurity, request.app.state.tokens)
    user_id = tokens.subject(credentials.credentials)
    await users.get(user_id)
    return user_id


CurrentUser = Annotated[UUID, Depends(current_user_id)]
Auth = Annotated[AuthService, Depends(get_auth_service)]
Users = Annotated[UserService, Depends(get_user_service)]
