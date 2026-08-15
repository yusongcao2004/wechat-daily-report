from datetime import date, datetime, time

from wechat_daily_report.analyzer import analyze_daily
from wechat_daily_report.models import Employee, Message, MessageType


def test_analyze_daily_marks_submitted_and_missing():
    employees = (
        Employee(name="张三", aliases=("三哥",)),
        Employee(name="李四", aliases=()),
    )
    messages = (
        Message(sender="三哥", sent_at=datetime(2026, 6, 2, 9, 30), message_type=MessageType.IMAGE),
        Message(sender="李四", sent_at=datetime(2026, 6, 2, 10, 0), message_type=MessageType.TEXT, text="项目进度正常"),
    )

    analysis = analyze_daily(
        employees=employees,
        messages=messages,
        report_date=date(2026, 6, 2),
        start_time=time(0, 0),
        report_time=time(20, 0),
        work_keywords=("项目", "进度"),
    )

    assert analysis.expected_count == 2
    assert analysis.submitted_count == 1
    assert analysis.missing_count == 1
    assert analysis.statuses[0].submitted is True
    assert analysis.statuses[1].submitted is False
    assert "李四" in analysis.work_summary[0]


def test_analyze_daily_flags_late_and_duplicate_submissions():
    employees = (Employee(name="王五", aliases=()),)
    messages = (
        Message(sender="王五", sent_at=datetime(2026, 6, 2, 8, 0), message_type=MessageType.IMAGE),
        Message(sender="王五", sent_at=datetime(2026, 6, 2, 9, 0), message_type=MessageType.IMAGE),
        Message(sender="王五", sent_at=datetime(2026, 6, 2, 21, 0), message_type=MessageType.IMAGE),
    )

    analysis = analyze_daily(
        employees=employees,
        messages=messages,
        report_date=date(2026, 6, 2),
        start_time=time(0, 0),
        report_time=time(20, 0),
        work_keywords=(),
    )

    status = analysis.statuses[0]
    assert status.submitted is True
    assert status.submit_count == 2
    assert status.late_submit_at == datetime(2026, 6, 2, 21, 0)
    assert any("重复提交" in item for item in analysis.anomalies)
