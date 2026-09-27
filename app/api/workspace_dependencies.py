from typing import Annotated

from fastapi import Depends, Query

from app.api.dependencies import get_uow
from app.api.schemas.common import Pagination
from app.repositories.protocols import UnitOfWork
from app.services.members import MemberService
from app.services.workspaces import WorkspaceService


def workspace_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> WorkspaceService:
    return WorkspaceService(uow)


def member_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> MemberService:
    return MemberService(uow)


Workspaces = Annotated[WorkspaceService, Depends(workspace_service)]
Members = Annotated[MemberService, Depends(member_service)]
Paging = Annotated[Pagination, Query()]
