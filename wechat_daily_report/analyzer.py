from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time

from .models import DailyAnalysis, Employee, EmployeeStatus, Message, MessageType


def analyze_daily(
    *,
    employees: tuple[Employee, ...],
    messages: tuple[Message, ...],
    report_date: date,
    start_time: time,
    report_time: time,
    work_keywords: tuple[str, ...],
    collection_errors: tuple[str, ...] = (),
) -> DailyAnalysis:
    active = tuple(e for e in employees if e.active)
    start_dt = datetime.combine(report_date, start_time)
    report_dt = datetime.combine(report_date, report_time)
    alias_map = _build_alias_map(active)

    image_submissions: dict[str, list[Message]] = defaultdict(list)
    late_submissions: dict[str, list[Message]] = defaultdict(list)
    mentions: dict[str, list[str]] = defaultdict(list)
    work_lines: list[str] = []
    anomalies: list[str] = []

    for message in sorted(messages, key=lambda m: m.sent_at):
        employee = _match_employee(message.sender, alias_map)
        in_report_window = start_dt <= message.sent_at <= report_dt
        after_report_window = report_dt < message.sent_at and message.sent_at.date() == report_date

        if employee and message.message_type == MessageType.IMAGE:
            if in_report_window:
                image_submissions[employee.name].append(message)
            elif after_report_window:
                late_submissions[employee.name].append(message)

        if message.message_type == MessageType.TEXT and message.text.strip():
            if _is_work_related(message.text, work_keywords):
                line = f"{message.sent_at.strftime('%H:%M')} {message.sender}: {_compact(message.text)}"
                work_lines.append(line)
                if employee:
                    mentions[employee.name].append(line)

    statuses: list[EmployeeStatus] = []
    for employee in active:
        submitted = image_submissions.get(employee.name, [])
        late = late_submissions.get(employee.name, [])
        notes: list[str] = []
        if len(submitted) > 1:
            notes.append(f"重复提交 {len(submitted)} 次")
            anomalies.append(f"{employee.name} 重复提交 {len(submitted)} 次")
        if not submitted and late:
            notes.append(f"20:00后迟交，首次迟交 {late[0].sent_at.strftime('%H:%M')}")
            anomalies.append(f"{employee.name} 20:00后迟交")

        statuses.append(
            EmployeeStatus(
                employee=employee,
                submitted=bool(submitted),
                first_submit_at=submitted[0].sent_at if submitted else None,
                submit_count=len(submitted),
                late_submit_at=late[0].sent_at if late else None,
                work_mentions=tuple(mentions.get(employee.name, [])[:5]),
                notes=tuple(notes),
            )
        )

    submitted_count = sum(1 for s in statuses if s.submitted)
    return DailyAnalysis(
        report_date=report_date.isoformat(),
        expected_count=len(active),
        submitted_count=submitted_count,
        missing_count=len(active) - submitted_count,
        statuses=tuple(statuses),
        work_summary=tuple(work_lines[:20]),
        anomalies=tuple(anomalies),
        collection_errors=collection_errors,
    )


def _build_alias_map(employees: tuple[Employee, ...]) -> dict[str, Employee]:
    alias_map: dict[str, Employee] = {}
    for employee in employees:
        for name in employee.all_names():
            key = _normalize_name(name)
            if key:
                alias_map[key] = employee
    return alias_map


def _match_employee(sender: str, alias_map: dict[str, Employee]) -> Employee | None:
    normalized = _normalize_name(sender)
    if normalized in alias_map:
        return alias_map[normalized]
    for alias, employee in alias_map.items():
        if alias and alias in normalized:
            return employee
    return None


def _normalize_name(value: str) -> str:
    return "".join(value.lower().split())


def _is_work_related(text: str, keywords: tuple[str, ...]) -> bool:
    if not keywords:
        return bool(text.strip())
    return any(keyword and keyword in text for keyword in keywords)


def _compact(text: str, max_len: int = 90) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= max_len:
        return compacted
    return compacted[: max_len - 1] + "…"
