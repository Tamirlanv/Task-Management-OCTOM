from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.api.schemas.common import InputModel, PatchModel

TagName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]
Color = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]


class TagCreate(InputModel):
    name: TagName
    color: Color | None = None


class TagUpdate(PatchModel):
    name: TagName | None = None
    color: Color | None = None


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workspace_id: UUID
    name: str
    color: str | None
