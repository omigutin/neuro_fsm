__all__ = ['RawHistoryWriter']

from ..configs.history_writer_config import HistoryWriterConfig
from .base_history_writer import BaseHistoryWriter


class RawHistoryWriter(BaseHistoryWriter):
    def __init__(self, config: HistoryWriterConfig):
        super().__init__(config, '.txt')

    def write(self, record: str) -> None:
        self._file.write(record + ' ')
        self._file.flush()
