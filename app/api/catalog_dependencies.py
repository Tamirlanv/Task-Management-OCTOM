from typing import Annotated

from fastapi import Depends

from app.api.dependencies import get_uow
from app.repositories.protocols import UnitOfWork
from app.services.projects import ProjectService
from app.services.tags import TagService


def project_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> ProjectService:
    return ProjectService(uow)


def tag_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> TagService:
    return TagService(uow)


Projects = Annotated[ProjectService, Depends(project_service)]
Tags = Annotated[TagService, Depends(tag_service)]
