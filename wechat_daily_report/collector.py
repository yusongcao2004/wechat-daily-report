from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, time

from .models import Message


class WeChatCollector(ABC):
    @abstractmethod
    def collect_messages(self, *, report_date: date, start_time: time, end_time: time) -> tuple[Message, ...]:
        raise NotImplementedError

    @abstractmethod
    def send_group_message(self, text: str) -> None:
        raise NotImplementedError
