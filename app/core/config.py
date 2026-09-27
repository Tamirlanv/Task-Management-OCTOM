from typing import Literal, Self

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: PostgresDsn
    redis_url: RedisDsn
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = Field(default="task-management-api", min_length=1)
    jwt_audience: str = Field(default="task-management-client", min_length=1)
    access_token_ttl_seconds: int = Field(default=900, ge=60, le=900)
    refresh_session_ttl_seconds: int = Field(default=2592000, ge=900, le=2592000)
    cors_origins: list[str] = Field(default_factory=list)
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=5, ge=0, le=100)
    db_pool_timeout_seconds: float = Field(default=5, gt=0, le=60)
    db_command_timeout_seconds: float = Field(default=10, gt=0, le=120)
    dependency_timeout_seconds: float = Field(default=2, gt=0, le=30)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    rate_login_per_ip: int = Field(default=30, ge=1)
    rate_login_per_account: int = Field(default=5, ge=1)
    rate_register_per_ip: int = Field(default=5, ge=1)
    rate_refresh_per_ip: int = Field(default=30, ge=1)
    rate_authenticated: int = Field(default=120, ge=1)
    rate_anonymous: int = Field(default=60, ge=1)

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        if self.database_url.scheme != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL must use postgresql+asyncpg")
        if any(origin == "*" for origin in self.cors_origins):
            raise ValueError("CORS_ORIGINS must contain explicit origins")
        if self.app_env == "production" and any(
            not origin.startswith("https://") for origin in self.cors_origins
        ):
            raise ValueError("Production CORS origins must use HTTPS")
        return self
