__all__ = ['HistoryWriterConfig']

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HistoryWriterConfig:
    name: str
    fields: tuple
    enable: bool = False
    max_age_days: int = 14
    async_mode: bool = False
