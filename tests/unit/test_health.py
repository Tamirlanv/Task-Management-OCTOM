import asyncio

import pytest

from app.services.errors import DependencyUnavailable
from app.services.health import ensure_ready


class Probe:
    def __init__(self, failure: str | None = None) -> None:
        self.failure = failure
        self.visited: set[str] = set()

    async def database(self) -> None:
        self.visited.add("database")
        if self.failure == "database":
            raise ConnectionError("private database credentials")

    async def cache(self) -> None:
        self.visited.add("cache")
        if self.failure == "cache":
            raise ConnectionError("private redis credentials")
        if self.failure == "timeout":
            await asyncio.Event().wait()


async def test_ready_checks_both_dependencies() -> None:
    probe = Probe()
    await ensure_ready(probe, 1)
    assert probe.visited == {"database", "cache"}


@pytest.mark.parametrize("failure", ["database", "cache", "timeout"])
async def test_readiness_fails_on_dependency_error(failure: str) -> None:
    with pytest.raises(DependencyUnavailable):
        await ensure_ready(Probe(failure), 0.01)


async def test_readiness_does_not_swallow_cancellation() -> None:
    task = asyncio.create_task(ensure_ready(Probe("timeout"), 10))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
