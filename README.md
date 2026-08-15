# WeChat Daily Report Checker

A fail-closed Windows desktop automation tool that reviews image-based daily
reports in a selected WeChat group, identifies missing or late submissions, and
produces a structured summary. It uses only the already logged-in WeChat desktop
window; it does not read or decrypt WeChat databases.

这是一个 Windows 微信群日报检查程序：每天读取指定群聊在设定时间段内的
图片日报，统计已交、未交、迟交和重复提交，并生成中文汇总。

This is an independent, unofficial project and is not affiliated with Tencent
or WeChat.

## Safety and privacy defaults

- Real group delivery is **off by default**.
- Sending requires all three gates: `send_report_to_group: true`,
  `runtime.dry_run: false`, and the explicit CLI flag `--send`.
- The scheduled-task installer creates a preview-only task unless
  `-EnableSend` is supplied.
- Real employee configuration, group names, screenshots, OCR evidence, reports,
  and logs are excluded from Git.
- The application works through the visible Windows UI and does not bypass
  login, encryption, or access controls.

## What it does

- Opens a configured WeChat group in the logged-in Windows client
- Captures a bounded number of visible message pages
- Uses local Tesseract OCR to extract timestamps, senders, and image markers
- Matches configured employee names and aliases
- Flags missing, late, and duplicate submissions
- Extracts a bounded work-related text summary using configured keywords
- Writes raw observations, analysis, evidence, and a Markdown report locally
- Optionally pastes the final report back into the group after explicit opt-in

## Requirements

- Windows 10 or 11
- Python 3.11+
- WeChat desktop already logged in
- Tesseract OCR with Chinese (`chi_sim`) and English language data
- An unlocked interactive desktop session while the collection runs

## Installation

```powershell
git clone https://github.com/<your-account>/wechat-daily-report.git
cd wechat-daily-report
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
copy employees.example.yaml employees.yaml
copy settings.example.yaml settings.yaml
```

If Tesseract is not on `PATH`, set its local path in `settings.yaml`:

```yaml
runtime:
  tesseract_cmd: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

## Configuration

`employees.yaml` contains real names and aliases and must remain local:

```yaml
employees:
  - name: 张三
    aliases: ["张三", "Zhang San"]
    active: true
```

`settings.yaml` defines the group, collection window, output paths, and delivery
gates. Start from the provided example, which is intentionally dry-run.

## Preview run

No flag is required for safe preview mode:

```powershell
python -m wechat_daily_report --settings settings.yaml --employees employees.yaml
```

The report is printed and saved locally, but is not sent to WeChat. `--dry-run`
is also available as an explicit override.

## Enabling group delivery

First inspect multiple preview runs. Then set both local configuration gates:

```yaml
wechat:
  send_report_to_group: true

runtime:
  dry_run: false
```

Real delivery still requires the command-line gate:

```powershell
python -m wechat_daily_report --settings settings.yaml --employees employees.yaml --send
```

## Windows Scheduled Task

Preview-only installation:

```powershell
.\install_windows_task.ps1 -ProjectDir (Get-Location).Path
```

Only after preview verification, explicitly install a send-enabled task:

```powershell
.\install_windows_task.ps1 -ProjectDir (Get-Location).Path -EnableSend
```

The task uses the current Windows user, requires an interactive desktop, and
runs with least privilege.

## Local output

Each run writes to `reports/YYYY-MM-DD/`:

- `messages.json`: OCR-derived observations
- `analysis.json`: employee-level submission status
- `report.md`: rendered group report
- `error.md`: failure report when collection cannot complete

Screenshots used as evidence are written under `evidence/`. These directories
may contain personal data and are ignored by Git.

## Tests

```powershell
python -m pytest -q
```

The unit tests cover report analysis, rendering, safe configuration defaults,
and the multi-gate delivery decision. GitHub Actions runs them on Windows with
Python 3.11 and 3.12.

## Known limits

- WeChat UI changes can break window discovery or OCR layout assumptions.
- OCR can misread sender names, timestamps, or image markers; reports require
  human review during rollout.
- The computer must remain awake, unlocked, and logged in to WeChat.
- The first version detects image submissions; it does not judge image quality
  or whether a report's content is truthful.
- Use is subject to organizational policy, consent requirements, WeChat terms,
  and applicable privacy law.

## License

Copyright (c) 2026. All rights reserved. The source is published for
portfolio review and personal reference; no reuse licence is granted.
