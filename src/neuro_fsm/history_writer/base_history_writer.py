__all__ = ['BaseHistoryWriter']

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, TextIO

from ..configs.history_writer_config import HistoryWriterConfig

logger = logging.getLogger(__name__)


class BaseHistoryWriter:
    """
        Базовый файловый писатель истории.
        Файл создаётся в каталоге ./fsm_logs (относительно рабочего каталога) и открывается при первой записи.
        При создании писателя удаляются файлы того же расширения старше max_age_days.
    """

    LOGS_DIR_NAME: str = 'fsm_logs'

    def __init__(self, config: HistoryWriterConfig, extension: str) -> None:
        if not config.name:
            raise ValueError(f"[{self.__class__.__name__}] File name is not set in HistoryWriterConfig")
        self._file: Optional[TextIO] = None
        self._fields: tuple[str, ...] = tuple(config.fields)
        self._path: str = self._resolve_log_path(config.name)
        self._cleanup_old_files(self._path, extension, config.max_age_days)

    @property
    def path(self) -> str:
        """ Полный путь к файлу лога. """
        return self._path

    def open(self) -> None:
        """ Открывает файл на дозапись, если он закрыт. """
        if self._file is None or self._file.closed:
            self._file = open(self._path, 'a', encoding='utf-8')

    def close(self) -> None:
        """ Закрывает файл, если он открыт. """
        if self._file is not None and not self._file.closed:
            self._file.close()

    def _write(self, text: str) -> None:
        """ Дописывает текст и сбрасывает буфер, чтобы лог не терялся при аварийном завершении. """
        if self._file is None or self._file.closed:
            self._file = open(self._path, 'a', encoding='utf-8')
        self._file.write(text)
        self._file.flush()

    @staticmethod
    def _cleanup_old_files(path: str, extension: str, max_age_days: int) -> None:
        """ Удаляет файлы с расширением extension старше max_age_days в каталоге лога. """
        dir_path = os.path.dirname(path) or '.'
        cutoff = datetime.now() - timedelta(days=max_age_days)
        for file_name in os.listdir(dir_path):
            if not file_name.endswith(extension):
                continue
            file_path = os.path.join(dir_path, file_name)
            try:
                if datetime.fromtimestamp(os.path.getmtime(file_path)) < cutoff:
                    os.remove(file_path)
            except OSError as exc:
                # Чужой или занятый файл не должен ломать запуск FSM
                logger.warning("Cannot remove old FSM log %s: %s", file_path, exc)

    @classmethod
    def _resolve_log_path(cls, file_name: str) -> str:
        """ Строит путь ./fsm_logs/<file_name> с подстановкой {timestamp} и создаёт каталог. """
        timestamp = datetime.now().strftime('%d%m%Y_%H%M')
        abs_path = os.path.join(os.getcwd(), cls.LOGS_DIR_NAME, file_name.format(timestamp=timestamp))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        return abs_path
