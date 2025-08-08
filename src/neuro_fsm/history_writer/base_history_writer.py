__all__ = ['BaseHistoryWriter']

import os
from datetime import datetime, timedelta
from io import TextIOWrapper
from typing import Any, Dict, Optional

from ..configs.history_writer_config import HistoryWriterConfig


class BaseHistoryWriter:
    def __init__(self, config: HistoryWriterConfig, frmt: str) -> None:
        """ Создаёт файловый писатель и очищает устаревшие логи. """
        self._file: Optional[TextIOWrapper] = None
        self._fields = config.fields
        self._async_mode = config.async_mode
        self._path = self._resolve_log_path(config.name)
        self._cleanup_old_files(self._path, frmt, config.max_age_days)
        self.open()

    def open(self):
        """Открывает файл, если он закрыт."""
        if self._file is None or self._file.closed:
            self._file = open(self._path, 'a', encoding='utf-8')

    def close(self) -> None:
        """ Закрывает файл если он открыт. """
        if self._file is not None and not self._file.closed:
            self._file.close()

    def write(self, record: Dict[str, Any]) -> None:
        raise NotImplementedError

    @staticmethod
    def _cleanup_old_files(path: str, fmt: str, max_age_days: int):
        """ Удаляет файлы старше max_age_days в директории path """
        dir_path = os.path.dirname(path) or '.'
        cutoff = datetime.now() - timedelta(days=max_age_days)
        for file_name in os.listdir(dir_path):
            if file_name.endswith(fmt):
                fpath = os.path.join(dir_path, file_name)
                try:
                    ctime = datetime.fromtimestamp(os.path.getctime(fpath))
                    if ctime < cutoff:
                        os.remove(fpath)
                except Exception:
                    pass

    @staticmethod
    def _resolve_log_path(file_name: str) -> str:
        # Получаем рабочую директорию (корень проекта)
        root_dir = os.getcwd()
        logs_dir = os.path.join(root_dir, 'fsm_logs')
        # Формируем подстановку даты/времени
        timestamp = datetime.now().strftime('%d%m%Y_%H%M')
        # Подставляем {timestamp}
        name = file_name.format(timestamp=timestamp)
        # Полный путь
        abs_path = os.path.join(logs_dir, name)
        # Создаём каталог, если его нет
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        return abs_path
