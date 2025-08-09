from __future__ import annotations

__all__ = ["AsyncRawHistoryWriter"]

from typing import Any, Dict, Iterable

from ..configs.history_writer_config import HistoryWriterConfig
from .base_history_writer import BaseHistoryWriter


class AsyncRawHistoryWriter(BaseHistoryWriter):
    """
        Асинхронный писатель сырой истории.
        - Пишет одну строку на запись.
        - Формат: "k1=v1; k2=v2; ..."
        - Зависимость aiofiles опциональна, проверяется лениво.
    """

    def __init__(self, config: HistoryWriterConfig) -> None:
        # Используем базовую подготовку пути/ротацию, но self._file не задействуем
        super().__init__(config, ".txt")

    # -------------------- Public Async API --------------------

    async def write(self, record: Dict[str, Any]) -> None:
        """
            Асинхронно дописывает строку в raw-лог.
            Args:
                record: словарь любых ключей/значений; если ключ отсутствует в self._fields,
                        он игнорируется. Порядок полей — как в конфиге.
        """
        try:
            import aiofiles  # noqa: WPS433
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "AsyncRawHistoryWriter requires 'aiofiles' to be installed."
            ) from exc

        line_parts = [f"{k}={record.get(k, '')}" for k in self._fields]
        line = "; ".join(line_parts)

        async with aiofiles.open(self._path, "a", encoding="utf-8") as f:
            await f.write(line + "\n")

    # -------------------- Forbidden Sync API --------------------

    def write_sync(self, *_: Iterable[Any]) -> None:  # pragma: no cover
        """Запрещено: у асинхронного писателя нет синхронной записи."""
        raise RuntimeError("Use 'await AsyncRawHistoryWriter.write(...)' for async mode.")
