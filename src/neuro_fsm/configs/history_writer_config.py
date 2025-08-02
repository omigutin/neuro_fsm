__all__ = ['HistoryWriterConfig']

from dataclasses import dataclass

from ..history_writer.history_writer_format import HistoryWriterFormat


@dataclass(frozen=True, slots=True)
class HistoryWriterConfig:
    path: str
    fields: tuple
    enable: bool = False
    format: HistoryWriterFormat = HistoryWriterFormat.TXT
    max_age_days: int = 14
    async_mode: bool = False
