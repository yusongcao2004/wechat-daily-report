from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

from .models import Employee


@dataclass(frozen=True)
class WeChatSettings:
    group_name: str
    send_report_to_group: bool
    max_scroll_pages: int
    ui_delay_seconds: float


@dataclass(frozen=True)
class ScheduleSettings:
    start_time: time
    report_time: time
    timezone: str


@dataclass(frozen=True)
class ReportSettings:
    title_suffix: str
    include_employee_details: bool
    work_keywords: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeSettings:
    output_dir: Path
    evidence_dir: Path
    dry_run: bool
    tesseract_cmd: str


@dataclass(frozen=True)
class Settings:
    wechat: WeChatSettings
    schedule: ScheduleSettings
    report: ReportSettings
    runtime: RuntimeSettings


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("Missing PyYAML. Install dependencies with: pip install -r requirements.txt") from exc

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def parse_hhmm(value: str) -> time:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"Expected HH:MM time, got {value!r}")
    hour, minute = int(parts[0]), int(parts[1])
    return time(hour=hour, minute=minute)


def load_settings(path: Path) -> Settings:
    root = load_yaml(path)
    wechat = root.get("wechat", {})
    schedule = root.get("schedule", {})
    report = root.get("report", {})
    runtime = root.get("runtime", {})

    base_dir = path.parent
    return Settings(
        wechat=WeChatSettings(
            group_name=str(wechat["group_name"]),
            send_report_to_group=bool(wechat.get("send_report_to_group", False)),
            max_scroll_pages=int(wechat.get("max_scroll_pages", 18)),
            ui_delay_seconds=float(wechat.get("ui_delay_seconds", 0.5)),
        ),
        schedule=ScheduleSettings(
            start_time=parse_hhmm(str(schedule.get("start_time", "00:00"))),
            report_time=parse_hhmm(str(schedule.get("report_time", "20:00"))),
            timezone=str(schedule.get("timezone", "local")),
        ),
        report=ReportSettings(
            title_suffix=str(report.get("title_suffix", "日报检查结果")),
            include_employee_details=bool(report.get("include_employee_details", True)),
            work_keywords=tuple(str(x) for x in report.get("work_keywords", [])),
        ),
        runtime=RuntimeSettings(
            output_dir=_resolve_path(base_dir, runtime.get("output_dir", "reports")),
            evidence_dir=_resolve_path(base_dir, runtime.get("evidence_dir", "evidence")),
            dry_run=bool(runtime.get("dry_run", True)),
            tesseract_cmd=str(runtime.get("tesseract_cmd", "")),
        ),
    )


def load_employees(path: Path) -> tuple[Employee, ...]:
    root = load_yaml(path)
    rows = root.get("employees", [])
    if not isinstance(rows, list):
        raise ValueError("employees.yaml must contain an employees list")

    employees: list[Employee] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each employee entry must be an object")
        name = str(row["name"]).strip()
        aliases = tuple(str(a).strip() for a in row.get("aliases", []) if str(a).strip())
        employees.append(
            Employee(
                name=name,
                aliases=aliases,
                active=bool(row.get("active", True)),
            )
        )

    if not employees:
        raise ValueError("No employees configured")
    return tuple(employees)


def _resolve_path(base_dir: Path, value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else base_dir / path
