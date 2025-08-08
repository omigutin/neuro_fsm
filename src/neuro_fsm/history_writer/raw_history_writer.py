__all__ = ['RawHistoryWriter']

from typing import Any, Dict

from ..configs.history_writer_config import HistoryWriterConfig
from .base_history_writer import BaseHistoryWriter


class RawHistoryWriter(BaseHistoryWriter):
    def __init__(self, config: HistoryWriterConfig):
        super().__init__(config, '.txt')

    def write(self, record: str) -> None:
        self._file.write(record + ' ')
        self._file.flush()

    async def async_write(self, record: Dict[str, Any]) -> None:
        import aiofiles
        line = "; ".join(f"{k}={record.get(k, '')}" for k in self._fields)
        async with aiofiles.open(self._path, 'a', encoding='utf-8') as f:
            await f.write(line + '\n')
