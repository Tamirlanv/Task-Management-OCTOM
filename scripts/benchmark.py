"""Load the disposable test environment; never accepts a production URL."""

import argparse
import asyncio
import json
import math
import platform
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import NAMESPACE_URL, UUID, uuid5

# asyncpg does not ship a py.typed marker; this adapter is confined to test seeding.
import asyncpg  # type: ignore[import-untyped]
from httpx import AsyncClient, HTTPError
from pydantic import PostgresDsn, RedisDsn, SecretStr
from redis.asyncio import Redis

from app.core.config import Settings
from app.core.security import TokenSecurity

DATABASE = "postgresql://taskman:test-only@127.0.0.1:55432/taskman_test"
API = "http://127.0.0.1:8001"


def identifier(kind: str, number: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"task-management/benchmark/{kind}/{number}")


async def seed() -> None:
    connection = await asyncpg.connect(DATABASE)
    try:
        async with connection.transaction():
            # This fixed endpoint is exclusively the disposable Compose test DB.
            await connection.execute(
                "TRUNCATE users, workspaces, session_families CASCADE"
            )
            await connection.executemany(
                "INSERT INTO users (id, email, name, password_hash) VALUES ($1, $2, $3, $4)",
                [
                    (
                        identifier("user", i),
                        f"bench-{i}@example.com",
                        f"User {i}",
                        "unusable-benchmark-password",
                    )
                    for i in range(100)
                ],
            )
            await connection.executemany(
                "INSERT INTO workspaces (id, name) VALUES ($1, $2)",
                [(identifier("workspace", i), f"Workspace {i}") for i in range(100)],
            )
            await connection.execute(
                "INSERT INTO workspace_memberships (workspace_id, user_id, role_id) SELECT w.id, u.id, r.id FROM workspaces w JOIN users u ON replace(w.name, 'Workspace ', '') = replace(u.name, 'User ', '') CROSS JOIN roles r WHERE r.name = 'Admin'"
            )
            await connection.executemany(
                "INSERT INTO projects (id, workspace_id, name, created_by) VALUES ($1, $2, $3, $4)",
                [
                    (
                        identifier("project", i),
                        identifier("workspace", i // 10),
                        f"Project {i}",
                        identifier("user", i // 10),
                    )
                    for i in range(1000)
                ],
            )
            now = datetime.now(UTC)
            for start in range(0, 100000, 5000):
                rows = [
                    (
                        identifier("task", i),
                        identifier("workspace", i // 1000),
                        identifier("project", i // 100),
                        f"Benchmark task {i}",
                        "Searchable benchmark description",
                        "todo",
                        ("low", "medium", "high", "urgent")[i % 4],
                        now + timedelta(days=i % 30 - 10),
                        identifier("user", i // 1000),
                    )
                    for i in range(start, start + 5000)
                ]
                await connection.copy_records_to_table(
                    "tasks",
                    records=rows,
                    columns=[
                        "id",
                        "workspace_id",
                        "project_id",
                        "title",
                        "description",
                        "status",
                        "priority",
                        "due_at",
                        "created_by",
                    ],
                )
        await connection.execute("ANALYZE")
    finally:
        await connection.close()
    redis = Redis(host="127.0.0.1", port=56379, db=15)
    try:
        await redis.flushdb()
    finally:
        await redis.aclose()


@dataclass
class Measurements:
    reads: list[float]
    writes: list[float]
    statuses: Counter[str]
    transport_errors: Counter[str]


def percentile(values: list[float], fraction: float) -> float:
    return (
        round(sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)], 2)
        if values
        else 0.0
    )


async def run_load(duration: int, rate: int) -> dict[str, object]:
    settings = Settings(
        app_env="test",
        database_url=PostgresDsn(
            DATABASE.replace("postgresql:", "postgresql+asyncpg:")
        ),
        redis_url=RedisDsn("redis://127.0.0.1:56379/15"),
        jwt_secret=SecretStr("test-only-secret-" * 4),
    )
    security = TokenSecurity(settings)
    headers = [
        {"Authorization": f"Bearer {security.access(identifier('user', i))}"}
        for i in range(100)
    ]
    readings = Measurements([], [], Counter(), Counter())
    gate = asyncio.Semaphore(200)
    async with AsyncClient(base_url=API, timeout=10) as client:

        async def request(sequence: int) -> None:
            async with gate:
                user = sequence % 100
                base = f"/api/v1/workspaces/{identifier('workspace', user)}/tasks"
                write = sequence % 5 == 0
                started = perf_counter()
                try:
                    if write:
                        task_id = identifier(
                            "task", user * 1000 + sequence // 100 % 1000
                        )
                        response = await client.patch(
                            f"{base}/{task_id}",
                            headers=headers[user],
                            json={"title": f"Updated {sequence}"},
                        )
                    else:
                        response = await client.get(
                            base, headers=headers[user], params={"limit": 20}
                        )
                    readings.statuses[str(response.status_code)] += 1
                except HTTPError as exc:
                    readings.statuses["transport_error"] += 1
                    readings.transport_errors[type(exc).__name__] += 1
                (readings.writes if write else readings.reads).append(
                    (perf_counter() - started) * 1000
                )

        started = perf_counter()
        pending = []
        for sequence in range(duration * rate):
            await asyncio.sleep(max(0, started + sequence / rate - perf_counter()))
            pending.append(asyncio.create_task(request(sequence)))
        await asyncio.gather(*pending)
        elapsed = perf_counter() - started
    failures = sum(count for code, count in readings.statuses.items() if code != "200")
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "duration_seconds": round(elapsed, 2),
        "requested_duration_seconds": duration,
        "target_rps": rate,
        "actual_rps": round(duration * rate / elapsed, 2),
        "requests": duration * rate,
        "statuses": dict(readings.statuses),
        "transport_error_types": dict(readings.transport_errors),
        "read_p95_ms": percentile(readings.reads, 0.95),
        "write_p95_ms": percentile(readings.writes, 0.95),
        "read_p99_ms": percentile(readings.reads, 0.99),
        "write_p99_ms": percentile(readings.writes, 0.99),
        "error_percent": round(failures / (duration * rate) * 100, 3),
        "dataset": {"workspaces": 100, "projects": 1000, "tasks": 100000, "users": 100},
        "resource_limits": {"api": "2 CPU / 2 GiB", "postgres": "2 CPU / 4 GiB"},
        "client_python": platform.python_version(),
        "packages": {
            package: version(package)
            for package in ("fastapi", "sqlalchemy", "asyncpg", "redis")
        },
        "scope": "Docker Desktop local benchmark; excludes login hashing and external network latency",
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=int, default=600)
    parser.add_argument("--rate", type=int, default=50)
    parser.add_argument("--output", type=Path, default=Path("docs/benchmark.json"))
    options = parser.parse_args()
    if not 1 <= options.duration <= 600 or not 1 <= options.rate <= 50:
        parser.error("duration must be 1..600 and rate must be 1..50")
    await seed()
    print("Seeded 100 workspaces, 1,000 projects and 100,000 tasks.", flush=True)
    report = await run_load(options.duration, options.rate)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
