import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from app.services.errors import DependencyUnavailable


class HealthProbe(Protocol):
    async def database(self) -> None: ...

    async def cache(self) -> None: ...


async def _available(
    check: Callable[[], Awaitable[None]], deadline_seconds: float
) -> bool:
    try:
        async with asyncio.timeout(deadline_seconds):
            await check()
    except Exception:
        # Dependency failures become an opaque readiness failure, never a success.
        return False
    return True


async def ensure_ready(probe: HealthProbe, deadline_seconds: float) -> None:
    database_ready, cache_ready = await asyncio.gather(
        _available(probe.database, deadline_seconds),
        _available(probe.cache, deadline_seconds),
    )
    if not database_ready or not cache_ready:
        raise DependencyUnavailable
