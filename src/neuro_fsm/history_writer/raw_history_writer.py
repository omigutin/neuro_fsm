__all__ = ['RawHistoryWriter']

from ..configs.history_writer_config import HistoryWriterConfig
from .base_history_writer import BaseHistoryWriter


class RawHistoryWriter(BaseHistoryWriter):
    """ Писатель сырой истории: все входные cls_id через пробел. """

    def __init__(self, config: HistoryWriterConfig) -> None:
        super().__init__(config, '.txt')

    def write(self, record: str) -> None:
        """ Дописывает одну запись. """
        self._write(record + ' ')
