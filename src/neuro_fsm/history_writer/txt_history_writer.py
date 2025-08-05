__all__ = ['TxtHistoryWriter']

from typing import List, Any, Dict

from .base_history_writer import BaseHistoryWriter
from ..configs.history_writer_config import HistoryWriterConfig


class TxtHistoryWriter(BaseHistoryWriter):
    def __init__(self, config: HistoryWriterConfig):
        self.fields = config.fields
        self.async_mode = config.async_mode
        self.path = self._resolve_log_path(config.path)
        self.file = open(self.path, 'a', encoding='utf-8')
        self._cleanup_old_files(self.path, '.txt', config.max_age_days)

    def write(self, record: str) -> None:
        self.file.write(record + ' ')
        self.file.flush()

    async def awrite(self, record: Dict[str, Any]) -> None:
        import aiofiles
        line = "; ".join(f"{k}={record.get(k, '')}" for k in self.fields)
        async with aiofiles.open(self.path, 'a', encoding='utf-8') as f:
            await f.write(line + '\n')

    def close(self) -> None:
        self.file.close()
