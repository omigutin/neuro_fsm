__all__ = ['TxtHistoryWriter']

from typing import List, Any, Dict

from .base_history_writer import BaseHistoryWriter
from ..configs.history_writer_config import HistoryWriterConfig


class TxtHistoryWriter(BaseHistoryWriter):
    def __init__(self, config: HistoryWriterConfig):
        self.path = config.path
        self.fields = config.fields
        self.async_mode = config.async_mode
        self.file = open(self.path, 'a', encoding='utf-8')
        self._cleanup_old_files(self.path, '.txt', config.max_age_days)

    def write(self, record: Dict[str, Any]) -> None:
        line = "; ".join(f"{k}={record.get(k, '')}" for k in self.fields)
        self.file.write(line + '\n')
        self.file.flush()

    async def awrite(self, record: Dict[str, Any]) -> None:
        import aiofiles
        line = "; ".join(f"{k}={record.get(k, '')}" for k in self.fields)
        async with aiofiles.open(self.path, 'a', encoding='utf-8') as f:
            await f.write(line + '\n')

    def close(self) -> None:
        self.file.close()
