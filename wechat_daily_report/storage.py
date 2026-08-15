from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .models import DailyAnalysis, Message


def prepare_run_dir(output_dir: Path, report_date: date) -> Path:
    run_dir = output_dir / report_date.isoformat()
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_messages(run_dir: Path, messages: tuple[Message, ...]) -> Path:
    path = run_dir / "messages.json"
    _write_json(path, messages)
    return path


def save_analysis(run_dir: Path, analysis: DailyAnalysis) -> Path:
    path = run_dir / "analysis.json"
    _write_json(path, analysis)
    return path


def save_report(run_dir: Path, report: str, filename: str = "report.md") -> Path:
    path = run_dir / filename
    path.write_text(report, encoding="utf-8")
    return path


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(_to_jsonable(value), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value
