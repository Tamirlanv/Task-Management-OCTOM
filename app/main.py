from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.exception_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.middleware import RequestContextMiddleware
from app.api.v1.router import router as api_router
from app.core.config import Settings
from app.core.database import create_database_engine
from app.core.logging import configure_logging
from app.core.metrics import Metrics
from app.core.rate_limit import RateLimiter
from app.core.resources import InfrastructureProbe
from app.core.security import PasswordSecurity, TokenSecurity


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(configuration.log_level)
        engine = create_database_engine(configuration)
        redis = Redis.from_url(
            str(configuration.redis_url),
            socket_timeout=configuration.dependency_timeout_seconds,
            socket_connect_timeout=configuration.dependency_timeout_seconds,
            decode_responses=True,
        )
        app.state.engine = engine
        app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        app.state.passwords = PasswordSecurity()
        app.state.tokens = TokenSecurity(configuration)
        app.state.redis = redis
        app.state.rate_limiter = RateLimiter(
            redis, configuration.jwt_secret.get_secret_value()
        )
        app.state.health_probe = InfrastructureProbe(engine, redis)
        try:
            yield
        finally:
            try:
                await redis.aclose()
            finally:
                await engine.dispose()

    app = FastAPI(title="Task Management API", version="0.1.0", lifespan=lifespan)
    app.state.settings = configuration
    app.state.metrics = Metrics()
    app.add_middleware(RequestContextMiddleware, metrics=app.state.metrics)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuration.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID"],
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(api_router)
    return app
