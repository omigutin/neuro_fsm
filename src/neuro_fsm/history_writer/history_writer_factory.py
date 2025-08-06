__all__ = ['HistoryWriterFactory']

from .csv_history_writer import CsvHistoryWriter
from neuro_fsm.models.history_writer_format import HistoryWriterFormat
from .json_history_writer import JsonHistoryWriter
from .txt_history_writer import TxtHistoryWriter
from ..configs.history_writer_config import HistoryWriterConfig


class HistoryWriterFactory:
    @staticmethod
    def create(config: HistoryWriterConfig):
        if config.format == HistoryWriterFormat.CSV:
            return CsvHistoryWriter(config)
        elif config.format == HistoryWriterFormat.JSON:
            return JsonHistoryWriter(config)
        elif config.format == HistoryWriterFormat.TXT:
            return TxtHistoryWriter(config)
        raise ValueError(f"Unknown writer format: {config.format.value}")
