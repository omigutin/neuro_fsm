__all__ = ['BaseHistoryWriter']

import os
from datetime import datetime, timedelta
from typing import Any, Dict


class BaseHistoryWriter:
    def write(self, record: Dict[str, Any]) -> None:
        raise NotImplementedError

    async def awrite(self, record: Dict[str, Any]) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass

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
    def _resolve_log_path(template: str) -> str:
        # Получаем рабочую директорию (корень проекта)
        root_dir = os.getcwd()
        logs_dir = os.path.join(root_dir, 'fsm_logs')
        # Формируем подстановку даты/времени
        timestamp = datetime.now().strftime('%d%m%Y_%H%M')
        # Подставляем {timestamp}
        name = template.format(timestamp=timestamp)
        # Полный путь
        abs_path = os.path.join(logs_dir, name)
        # Создаём каталог, если его нет
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        return abs_path
