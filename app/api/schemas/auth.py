from typing import Annotated, Literal

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.api.schemas.common import InputModel, Name

Password = Annotated[str, Field(min_length=12, max_length=128)]


class LoginInput(InputModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class RegisterInput(LoginInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "alice@example.com",
                    "name": "Alice",
                    "password": "replace-with-a-unique-password",
                }
            ]
        }
    )
    name: Name
    password: Password


class RefreshInput(InputModel):
    refresh_token: Annotated[str, Field(min_length=32, max_length=256)]


class TokenResponse(InputModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
