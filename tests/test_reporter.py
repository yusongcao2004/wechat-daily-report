from datetime import date, datetime, time

from wechat_daily_report.analyzer import analyze_daily
from wechat_daily_report.models import Employee, Message, MessageType
from wechat_daily_report.reporter import render_report


def test_render_report_contains_missing_names_and_summary():
    analysis = analyze_daily(
        employees=(
            Employee(name="张三", aliases=()),
            Employee(name="李四", aliases=()),
        ),
        messages=(
            Message(sender="张三", sent_at=datetime(2026, 6, 2, 9, 30), message_type=MessageType.IMAGE),
            Message(sender="李四", sent_at=datetime(2026, 6, 2, 11, 0), message_type=MessageType.TEXT, text="客户项目有风险"),
        ),
        report_date=date(2026, 6, 2),
        start_time=time(0, 0),
        report_time=time(20, 0),
        work_keywords=("客户", "风险"),
    )

    report = render_report(analysis, "日报检查结果")

    assert "2026-06-02 日报检查结果" in report
    assert "未提交名单" in report
    assert "李四" in report
    assert "客户项目有风险" in report
