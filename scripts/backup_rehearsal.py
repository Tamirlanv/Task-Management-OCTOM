"""Dump and restore only the disposable task-management-test PostgreSQL service."""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

COUNTS = """SELECT json_build_object(
    'users', (SELECT count(*) FROM users),
    'workspaces', (SELECT count(*) FROM workspaces),
    'projects', (SELECT count(*) FROM projects),
    'tasks', (SELECT count(*) FROM tasks),
    'roles', (SELECT count(*) FROM roles),
    'revision', (SELECT version_num FROM alembic_version))"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", default="docker")
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    prefix = [
        options.docker,
        "compose",
        "-f",
        str(root / "compose.test.yaml"),
        "exec",
        "-T",
        "postgres",
    ]

    def run(*arguments: str) -> str:
        result = subprocess.run(
            [*prefix, *arguments], check=True, capture_output=True, text=True, cwd=root
        )
        return result.stdout.strip()

    token = uuid4().hex[:12]
    destination = f"taskman_restore_{token}"
    dump = f"/tmp/taskman-rehearsal-{token}.dump"
    before = json.loads(
        run("psql", "-U", "taskman", "-d", "taskman_test", "-tAc", COUNTS)
    )
    started = perf_counter()
    run(
        "pg_dump",
        "-U",
        "taskman",
        "-d",
        "taskman_test",
        "--format=custom",
        "--file",
        dump,
    )
    dump_seconds = perf_counter() - started
    run("createdb", "-U", "taskman", destination)
    try:
        started = perf_counter()
        run(
            "pg_restore",
            "-U",
            "taskman",
            "--no-owner",
            "--exit-on-error",
            "--dbname",
            destination,
            dump,
        )
        restore_seconds = perf_counter() - started
        restored = json.loads(
            run("psql", "-U", "taskman", "-d", destination, "-tAc", COUNTS)
        )
        if restored != before:
            raise RuntimeError("Restored row counts or migration revision differ")
        report = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "source": "taskman_test",
            "dump_seconds": round(dump_seconds, 3),
            "restore_seconds": round(restore_seconds, 3),
            "verified_counts": restored,
            "result": "passed",
            "scope": "Local disposable database; production storage and RPO/RTO are not certified",
        }
        target = root / "docs" / "backup-rehearsal.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    finally:
        # Only this invocation's newly created restore database is removed.
        run("dropdb", "-U", "taskman", destination)


if __name__ == "__main__":
    main()
