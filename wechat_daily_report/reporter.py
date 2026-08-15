from __future__ import annotations

from .models import DailyAnalysis


def render_report(analysis: DailyAnalysis, title_suffix: str, include_employee_details: bool = True) -> str:
    submitted = [s for s in analysis.statuses if s.submitted]
    missing = [s for s in analysis.statuses if not s.submitted]

    lines: list[str] = [
        f"{analysis.report_date} {title_suffix}",
        "",
        f"应交：{analysis.expected_count} 人；已交：{analysis.submitted_count} 人；未交：{analysis.missing_count} 人。",
        "",
        "未提交名单：",
        _names(missing) if missing else "无",
        "",
        "已提交名单：",
    ]

    if submitted:
        for status in submitted:
            submit_time = status.first_submit_at.strftime("%H:%M") if status.first_submit_at else "-"
            count_note = f"，共 {status.submit_count} 次" if status.submit_count > 1 else ""
            lines.append(f"- {status.employee.name}：{submit_time}{count_note}")
    else:
        lines.append("无")

    lines.extend(["", "异常："])
    if analysis.anomalies or analysis.collection_errors:
        for item in (*analysis.collection_errors, *analysis.anomalies):
            lines.append(f"- {item}")
    else:
        lines.append("无")

    lines.extend(["", "群内工作相关摘要："])
    if analysis.work_summary:
        lines.extend(f"- {item}" for item in analysis.work_summary)
    else:
        lines.append("无明显工作相关消息")

    if include_employee_details:
        lines.extend(["", "员工情况："])
        for status in analysis.statuses:
            state = "已提交" if status.submitted else "未提交"
            submit_time = status.first_submit_at.strftime("%H:%M") if status.first_submit_at else "-"
            notes = "；".join(status.notes) if status.notes else "-"
            mentions = " / ".join(status.work_mentions) if status.work_mentions else "-"
            lines.append(f"- {status.employee.name}：{state}，提交时间：{submit_time}，动态：{mentions}，备注：{notes}")

    return "\n".join(lines).strip() + "\n"


def render_error_report(report_date: str, error: Exception) -> str:
    return (
        f"{report_date} 日报检查失败\n\n"
        f"原因：{type(error).__name__}: {error}\n\n"
        "请人工检查微信是否已登录、群聊名称是否正确、电脑是否锁屏、OCR是否可用。\n"
    )


def _names(statuses) -> str:
    return "、".join(status.employee.name for status in statuses)
