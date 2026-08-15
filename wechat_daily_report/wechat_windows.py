from __future__ import annotations

import platform
import re
import time as time_module
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

from .collector import WeChatCollector
from .models import Message, MessageType


@dataclass(frozen=True)
class WeChatWindowsOptions:
    group_name: str
    max_scroll_pages: int
    ui_delay_seconds: float
    evidence_dir: Path
    tesseract_cmd: str = ""


class WeChatWindowsCollector(WeChatCollector):
    def __init__(self, options: WeChatWindowsOptions) -> None:
        self.options = options

    def collect_messages(self, *, report_date: date, start_time: time, end_time: time) -> tuple[Message, ...]:
        _require_windows()
        deps = _load_windows_deps(self.options.tesseract_cmd)
        app_window = self._open_group(deps)
        self.options.evidence_dir.mkdir(parents=True, exist_ok=True)

        seen: dict[str, Message] = {}
        for page in range(self.options.max_scroll_pages):
            screenshot = app_window.capture_as_image()
            evidence_path = self.options.evidence_dir / f"{report_date.isoformat()}_{page:02d}.png"
            screenshot.save(evidence_path)
            ocr_text = deps.pytesseract.image_to_string(screenshot, lang="chi_sim+eng")
            for message in parse_ocr_messages(ocr_text, report_date):
                if message.sent_at.date() == report_date:
                    key = f"{message.sent_at.isoformat()}|{message.sender}|{message.message_type}|{message.text}"
                    seen[key] = message
            deps.pyautogui.scroll(5)
            time_module.sleep(self.options.ui_delay_seconds)

        return tuple(sorted(seen.values(), key=lambda m: m.sent_at))

    def send_group_message(self, text: str) -> None:
        _require_windows()
        deps = _load_windows_deps(self.options.tesseract_cmd)
        self._open_group(deps)
        deps.pyperclip.copy(text)
        deps.pyautogui.hotkey("ctrl", "v")
        time_module.sleep(self.options.ui_delay_seconds)
        deps.pyautogui.press("enter")

    def _open_group(self, deps):
        app = deps.Application(backend="uia").connect(title_re=".*微信.*|.*WeChat.*", timeout=10)
        window = app.top_window()
        window.set_focus()
        time_module.sleep(self.options.ui_delay_seconds)

        deps.pyautogui.hotkey("ctrl", "f")
        time_module.sleep(self.options.ui_delay_seconds)
        deps.pyperclip.copy(self.options.group_name)
        deps.pyautogui.hotkey("ctrl", "v")
        time_module.sleep(self.options.ui_delay_seconds)
        deps.pyautogui.press("enter")
        time_module.sleep(self.options.ui_delay_seconds * 2)
        return window


def parse_ocr_messages(ocr_text: str, report_date: date) -> tuple[Message, ...]:
    messages: list[Message] = []
    current_sender = ""
    current_time: datetime | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_sender, current_time
        if not current_sender or not current_time or not buffer:
            buffer = []
            return
        text = " ".join(line.strip() for line in buffer if line.strip())
        message_type = _detect_message_type(text)
        messages.append(
            Message(
                sender=current_sender,
                sent_at=current_time,
                message_type=message_type,
                text="" if message_type == MessageType.IMAGE else text,
                raw={"ocr_text": text},
            )
        )
        buffer = []

    for raw_line in ocr_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        header = _parse_header(line, report_date)
        if header:
            flush()
            current_sender, current_time = header
            remainder = _strip_header(line)
            if remainder:
                buffer.append(remainder)
        else:
            buffer.append(line)
    flush()
    return tuple(messages)


def _parse_header(line: str, report_date: date) -> tuple[str, datetime] | None:
    patterns = [
        r"^(?P<time>\d{1,2}:\d{2})\s+(?P<sender>[^:：]{1,32})[:：]?\s*(?P<body>.*)$",
        r"^(?P<sender>[^:：]{1,32})\s+(?P<time>\d{1,2}:\d{2})[:：]?\s*(?P<body>.*)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, line)
        if not match:
            continue
        hour, minute = [int(x) for x in match.group("time").split(":")]
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            continue
        sender = match.group("sender").strip()
        if sender in {"微信", "WeChat"}:
            continue
        return sender, datetime.combine(report_date, time(hour=hour, minute=minute))
    return None


def _strip_header(line: str) -> str:
    line = re.sub(r"^\d{1,2}:\d{2}\s+[^:：]{1,32}[:：]?\s*", "", line)
    line = re.sub(r"^[^:：]{1,32}\s+\d{1,2}:\d{2}[:：]?\s*", "", line)
    return line.strip()


def _detect_message_type(text: str) -> MessageType:
    normalized = text.lower()
    image_markers = ("[图片]", "图片", "jpg", "jpeg", ".jpg", ".jpeg", "image")
    if any(marker in normalized for marker in image_markers):
        return MessageType.IMAGE
    return MessageType.TEXT if text else MessageType.UNKNOWN


def _require_windows() -> None:
    if platform.system().lower() != "windows":
        raise RuntimeError("WeChat Windows collection can only run on Windows")


def _load_windows_deps(tesseract_cmd: str):
    try:
        import pyautogui
        import pyperclip
        import pytesseract
        from pywinauto.application import Application
    except ImportError as exc:
        raise RuntimeError("Missing Windows automation dependencies. Run: pip install -r requirements.txt") from exc
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    class Deps:
        pass

    deps = Deps()
    deps.pyautogui = pyautogui
    deps.pyperclip = pyperclip
    deps.pytesseract = pytesseract
    deps.Application = Application
    return deps
