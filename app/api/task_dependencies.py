from typing import Annotated

from fastapi import Depends, Query

from app.api.dependencies import get_uow
from app.api.schemas.tasks import TaskFilters
from app.repositories.protocols import UnitOfWork
from app.services.tasks import TaskService


def task_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> TaskService:
    return TaskService(uow)


Tasks = Annotated[TaskService, Depends(task_service)]
Filters = Annotated[TaskFilters, Query()]
