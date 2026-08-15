from pathlib import Path

from wechat_daily_report.cli import delivery_enabled
from wechat_daily_report.config import load_settings


def test_example_settings_fail_closed():
    project_root = Path(__file__).resolve().parents[1]
    settings = load_settings(project_root / "settings.example.yaml")

    assert settings.wechat.send_report_to_group is False
    assert settings.runtime.dry_run is True


def test_delivery_requires_both_configuration_and_cli_opt_in():
    assert not delivery_enabled(
        config_enabled=True,
        config_dry_run=False,
        cli_send=False,
        cli_dry_run=False,
    )
    assert not delivery_enabled(
        config_enabled=False,
        config_dry_run=False,
        cli_send=True,
        cli_dry_run=False,
    )
    assert not delivery_enabled(
        config_enabled=True,
        config_dry_run=True,
        cli_send=True,
        cli_dry_run=False,
    )
    assert delivery_enabled(
        config_enabled=True,
        config_dry_run=False,
        cli_send=True,
        cli_dry_run=False,
    )
