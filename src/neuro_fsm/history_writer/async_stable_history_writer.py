from __future__ import annotations

__all__ = ["AsyncStableHistoryWriter"]

from typing import Any, Dict, Iterable, Sequence, TYPE_CHECKING

from ..configs.history_writer_config import HistoryWriterConfig
from .base_history_writer import BaseHistoryWriter

if TYPE_CHECKING:
    from ..core.profiles.profile import Profile, ProfileDict
    from ..core.states.state import State


class AsyncStableHistoryWriter(BaseHistoryWriter):
    """
        Асинхронный писатель стабильной истории в YAML-подобном формате.
        Поддерживает те же логические операции, что и синхронный StableHistoryWriter,
        но методы имеют префикс/семантику async.
    """

    def __init__(self, config: HistoryWriterConfig) -> None:
        super().__init__(config, ".yaml")
        self._events_started: bool = False

    # -------------------- Async writing helpers --------------------

    async def _awrite(self, text: str) -> None:
        try:
            import aiofiles  # noqa: WPS433
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "AsyncStableHistoryWriter requires 'aiofiles' to be installed."
            ) from exc

        async with aiofiles.open(self._path, "a", encoding="utf-8") as f:
            await f.write(text)

    # -------------------- Public Async API --------------------

    async def write_configs(self, record: Dict[str, Any]) -> None:
        """
            Один раз пишет общие настройки FSM.
        """
        await self._awrite("FSM_CONFIGURATION:\n")
        for key, value in record.items():
            await self._awrite(f"    {key}: {value}\n")
        await self._awrite("\n==============================\n\n")

    async def write_profile_configs(self, profiles: "ProfileDict") -> None:
        """
            Один раз выводит конфигурацию всех профилей.
        """
        await self._awrite("PROFILES_CONFIGURATION:\n\n")
        for profile in profiles.values():
            await self._awrite(f"PROFILE_NAME: '{profile.name}'\n")
            await self._awrite("\tSTATES:\n")
            for state in profile.states.values():
                await self._awrite(
                    f"\t\t{{cls_id: {state.cls_id}, name: '{state.name}', "
                    f"stable_min_lim: {state.stable_min_lim}, resettable: {state.is_resettable}}}\n"
                )
            init_states = ", ".join(s.name for s in profile.init_states)
            await self._awrite(f"    INIT_STATES: ({init_states}, )\n")
            default_states = ", ".join(s.name for s in profile.default_states)
            await self._awrite(f"    DEFAULT_STATES: ({default_states}, )\n")
            await self._awrite("\n")
        await self._awrite("\n==============================\n\n")

    async def start_events(self) -> None:
        """
            Ленивая секция EVENTS.
        """
        if not self._events_started:
            await self._awrite("EVENTS:\n")
            self._events_started = True

    async def write_event(
        self,
        *,
        timestamp: float,
        active_profile: "Profile",
        state: "State",
        frame_number: int | None = None,
    ) -> None:
        """
            Пишет одну событие-строку в секцию EVENTS.
            Формат выдержан по смыслу синхронной версии.
        """
        await self.start_events()
        dt = f"{timestamp:.3f}"
        counters_txt = self._format_counters(active_profile)
        history_txt = self._format_history(active_profile)
        suffix = f" frame={frame_number}" if frame_number is not None else ""
        await self._awrite(
            f"  - time: {dt}{suffix}; profile: {active_profile.name}; "
            f"state: {state.name}; counters: [{counters_txt}]; history: [{history_txt}]\n"
        )

    # -------------------- Formatting (pure) --------------------

    @staticmethod
    def _format_counters(profile: "Profile") -> str:
        counters = profile.counters.as_dict()
        parts = [f"{state.name}: {counters[state.cls_id]}" for state in profile.states.values()]
        return ", ".join(parts)

    @staticmethod
    def _format_history(profile: "Profile") -> str:
        names = [state.name for state in profile.history]
        return ", ".join(names) + (", " if names else "")

    # -------------------- Forbidden Sync API --------------------

    def write(self, *_: Iterable[Any]) -> None:  # pragma: no cover
        """Запрещено: используйте async-методы."""
        raise RuntimeError("Use async methods of AsyncStableHistoryWriter.")
