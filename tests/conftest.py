import pytest
from pydantic import PostgresDsn, RedisDsn, SecretStr

from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        database_url=PostgresDsn(
            "postgresql+asyncpg://taskman:test-only@127.0.0.1:55432/taskman_test"
        ),
        redis_url=RedisDsn("redis://127.0.0.1:56379/15"),
        jwt_secret=SecretStr("test-only-secret-" * 4),
        cors_origins=["http://localhost:5173"],
    )
