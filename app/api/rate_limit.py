from typing import Annotated, cast

from fastapi import Depends, Request

from app.api.dependencies import get_settings
from app.api.schemas.auth import LoginInput
from app.core.rate_limit import RateLimiter
from app.core.security import TokenSecurity
from app.services.errors import Unauthenticated


def get_limiter(request: Request) -> RateLimiter:
    return cast(RateLimiter, request.app.state.rate_limiter)


def client_ip(request: Request) -> str:
    # Uvicorn accepts forwarded headers only from explicitly trusted proxies.
    return request.client.host if request.client is not None else "unknown"


async def enforce_api_limit(
    request: Request, limiter: Annotated[RateLimiter, Depends(get_limiter)]
) -> None:
    settings = get_settings(request)
    ip = client_ip(request)
    routes = {
        "/api/v1/auth/login": ("login", settings.rate_login_per_ip, 60),
        "/api/v1/auth/register": ("register", settings.rate_register_per_ip, 3600),
        "/api/v1/auth/refresh": ("refresh", settings.rate_refresh_per_ip, 60),
    }
    if request.url.path in routes:
        kind, limit, window = routes[request.url.path]
        await limiter.check(f"{kind}:ip:{ip}", limit, window)
        return
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            user = cast(TokenSecurity, request.app.state.tokens).subject(token)
        except Unauthenticated:
            await limiter.check(f"anonymous:{ip}", settings.rate_anonymous)
            raise
        await limiter.check(f"user:{user}", settings.rate_authenticated)
        return
    await limiter.check(f"anonymous:{ip}", settings.rate_anonymous)


async def enforce_login_limit(
    request: Request,
    body: LoginInput,
    limiter: Annotated[RateLimiter, Depends(get_limiter)],
) -> None:
    await limiter.check(
        f"login:account:{client_ip(request)}:{body.email}",
        get_settings(request).rate_login_per_account,
    )
