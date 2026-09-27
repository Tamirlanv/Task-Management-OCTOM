from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreationDay:
    date: date
    count: int


@dataclass(frozen=True, slots=True)
class Overview:
    total: int
    done: int
    in_progress: int
    overdue: int
    projects: int
    days: list[CreationDay]


class Analytics(Protocol):
    async def overview(self, workspace_id: UUID, now: datetime) -> Overview: ...
