from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Employee:
    name: str
    aliases: tuple[str, ...]
    active: bool = True

    def all_names(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


@dataclass(frozen=True)
class Message:
    sender: str
    sent_at: datetime
    message_type: MessageType
    text: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmployeeStatus:
    employee: Employee
    submitted: bool
    first_submit_at: datetime | None = None
    submit_count: int = 0
    late_submit_at: datetime | None = None
    work_mentions: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DailyAnalysis:
    report_date: str
    expected_count: int
    submitted_count: int
    missing_count: int
    statuses: tuple[EmployeeStatus, ...]
    work_summary: tuple[str, ...]
    anomalies: tuple[str, ...]
    collection_errors: tuple[str, ...] = ()
