__all__ = ['CsvHistoryWriter']

import csv
import datetime
from typing import Any, Optional

from .base_history_writer import BaseHistoryWriter
from ..configs.history_writer_config import HistoryWriterConfig


class CsvHistoryWriter(BaseHistoryWriter):
    def __init__(self, config: HistoryWriterConfig):
        self._f = open(config.path, mode, newline='', encoding='utf-8')
        self._writer = csv.writer(self._f)
        # Можно добавить заголовок, если файл пустой:
        if self._f.tell() == 0:
            self._writer.writerow(["event_type", "value", "timestamp"])

    def write_state(self, state: Any, timestamp: Optional[float] = None) -> None:
        self._writer.writerow([
            "state",
            str(state),
            timestamp or datetime.datetime.now().timestamp()
        ])

    def write_profile_switch(self, profile_name: str, timestamp: Optional[float] = None) -> None:
        self._writer.writerow([
            "profile_switch",
            profile_name,
            timestamp or datetime.datetime.now().timestamp()
        ])

    def flush(self) -> None:
        self._f.flush()

    def close(self) -> None:
        self._f.close()