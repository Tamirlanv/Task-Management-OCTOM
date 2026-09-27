from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.api.schemas.common import Description, InputModel, Name, PatchModel
from app.services.contracts import Role


class WorkspaceCreate(InputModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Product launch",
                    "description": "Plan the next release",
                }
            ]
        }
    )
    name: Name
    description: Description = ""


class WorkspaceUpdate(PatchModel):
    name: Name | None = None
    description: Description | None = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class MemberCreate(InputModel):
    email: EmailStr
    role: Role = Role.MEMBER

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class MemberUpdate(InputModel):
    role: Role


class MemberResponse(BaseModel):
    user_id: UUID
    name: str
    role: Role
