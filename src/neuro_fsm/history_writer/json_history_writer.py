__all__ = ['JsonHistoryWriter']

import json
from typing import Any, List, Dict

from .base_history_writer import BaseHistoryWriter
from ..configs.history_writer_config import HistoryWriterConfig


class JsonHistoryWriter(BaseHistoryWriter):
    def __init__(self, config: HistoryWriterConfig):
        self.path = config.path
        self.fields = config.fields
        self.async_mode = config.async_mode
        self._cleanup_old_files(self.path, '.json', config.max_age_days)

    def write(self, record: Dict[str, Any]) -> None:
        filtered = {k: record.get(k, None) for k in self.fields}
        with open(self.path, 'a', encoding='utf-8') as f:
            json.dump(filtered, f, ensure_ascii=False)
            f.write('\n')

    async def awrite(self, record: Dict[str, Any]) -> None:
        import aiofiles
        filtered = {k: record.get(k, None) for k in self.fields}
        async with aiofiles.open(self.path, 'a', encoding='utf-8') as f:
            await f.write(json.dumps(filtered, ensure_ascii=False) + '\n')
