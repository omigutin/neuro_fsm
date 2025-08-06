__all__ = ['HistoryWriterFormat']

from enum import Enum


class HistoryWriterFormat(str, Enum):
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    YAML = "yaml"
