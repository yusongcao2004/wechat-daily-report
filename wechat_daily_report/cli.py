from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .analyzer import analyze_daily
from .config import load_employees, load_settings
from .reporter import render_error_report, render_report
from .storage import prepare_run_dir, save_analysis, save_messages, save_report
from .wechat_windows import WeChatWindowsCollector, WeChatWindowsOptions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Windows WeChat group daily image reports.")
    parser.add_argument("--settings", type=Path, default=Path("settings.yaml"))
    parser.add_argument("--employees", type=Path, default=Path("employees.yaml"))
    delivery = parser.add_mutually_exclusive_group()
    delivery.add_argument(
        "--send",
        action="store_true",
        help="Allow sending only when the settings file also enables it and disables dry-run.",
    )
    delivery.add_argument("--dry-run", action="store_true", help="Explicitly prevent WeChat delivery.")
    args = parser.parse_args(argv)

    settings = load_settings(args.settings)
    employees = load_employees(args.employees)
    report_date = datetime.now().date()
    run_dir = prepare_run_dir(settings.runtime.output_dir, report_date)
    evidence_dir = settings.runtime.evidence_dir / report_date.isoformat()

    collector = WeChatWindowsCollector(
        WeChatWindowsOptions(
            group_name=settings.wechat.group_name,
            max_scroll_pages=settings.wechat.max_scroll_pages,
            ui_delay_seconds=settings.wechat.ui_delay_seconds,
            evidence_dir=evidence_dir,
            tesseract_cmd=settings.runtime.tesseract_cmd,
        )
    )

    try:
        messages = collector.collect_messages(
            report_date=report_date,
            start_time=settings.schedule.start_time,
            end_time=settings.schedule.report_time,
        )
        save_messages(run_dir, messages)
        analysis = analyze_daily(
            employees=employees,
            messages=messages,
            report_date=report_date,
            start_time=settings.schedule.start_time,
            report_time=settings.schedule.report_time,
            work_keywords=settings.report.work_keywords,
        )
        save_analysis(run_dir, analysis)
        report = render_report(
            analysis,
            title_suffix=settings.report.title_suffix,
            include_employee_details=settings.report.include_employee_details,
        )
        save_report(run_dir, report)

        should_send = delivery_enabled(
            config_enabled=settings.wechat.send_report_to_group,
            config_dry_run=settings.runtime.dry_run,
            cli_send=args.send,
            cli_dry_run=args.dry_run,
        )
        if should_send:
            collector.send_group_message(report)
        else:
            print(report)
        return 0
    except Exception as exc:
        error_report = render_error_report(report_date.isoformat(), exc)
        save_report(run_dir, error_report, filename="error.md")
        print(error_report)
        return 2


def delivery_enabled(
    *,
    config_enabled: bool,
    config_dry_run: bool,
    cli_send: bool,
    cli_dry_run: bool,
) -> bool:
    """Require explicit agreement from both local configuration and the command line."""
    return config_enabled and not config_dry_run and cli_send and not cli_dry_run
