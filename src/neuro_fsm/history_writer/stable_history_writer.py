__all__ = ['StableHistoryWriter']

from datetime import datetime
from typing import Any, Dict, Iterable, Sequence

from ..configs.history_writer_config import HistoryWriterConfig
from ..core.profiles.profile import Profile
from ..core.profiles.types import ProfileDict
from ..core.states import State
from .base_history_writer import BaseHistoryWriter


class StableHistoryWriter(BaseHistoryWriter):
    """ Писатель стабильной истории в YAML-подобном формате.  """

    def __init__(self, config: HistoryWriterConfig) -> None:
        super().__init__(config, '.yaml')
        self._events_started = False

    def write_configs(self, record: Dict[str, Any]) -> None:
        """Записывает общие настройки FSM."""
        self._file.write('FSM_CONFIGURATION:\n')
        for key, value in record.items():
            self._file.write(f"    {key}: {value}\n")
        self._file.write('\n==============================\n\n')
        self._file.flush()

    def write_profile_configs(self, profiles: ProfileDict) -> None:
        """Выводит конфигурацию всех профилей единожды."""
        self._file.write('PROFILES_CONFIGURATION:\n\n')
        for profile in profiles.values():
            self._file.write(f"PROFILE_NAME: '{profile.name}'\n")
            self._file.write('\tSTATES:\n')
            for state in profile.states.values():
                self._file.write(
                    f"\t\t{{cls_id: {state.cls_id}, name: '{state.name}', "
                    f"stable_min_lim: {state.stable_min_lim}, resettable: {state.is_resettable}}}\n"
                )
            init_states = ', '.join(s.name for s in profile.init_states)
            self._file.write(f"    INIT_STATES: ({init_states}, )\n")
            default_states = ', '.join(s.name for s in profile.default_states)
            self._file.write(f"    DEFAULT_STATES: ({default_states}, )\n")
            self._file.write('    EXPECTED_SEQUENCES:\n')
            for seq in profile.history.expected_sequences:
                seq_str = ', '.join(s.name for s in seq)
                self._file.write(f"\t\t{seq_str}),\n")
            self._file.write('\n')
        self._file.write('==============================\n\n')
        self._file.flush()

    def write_state(self, state: State) -> None:
        """Записывает событие состояния."""
        self.open()
        self._ensure_events()
        timestamp = datetime.now().strftime('%H:%M:%S')
        self._file.write(f"    state: \"{state.name} [{timestamp}]\"\n")
        self._file.flush()

    def write_action(self, action: str, profiles: Sequence[str]) -> None:
        """Записывает событие действия."""
        self.open()
        self._ensure_events()
        self._file.write('    action:\n')
        self._file.write(f"        {action}: [{', '.join(profiles)}]\n")
        self._file.flush()

    def write_runtime(self, active: Profile, profiles: Iterable[Profile]) -> None:
        """ Фиксирует текущее состояние всех профилей. """
        self._file.write('------------------------------\n\n')
        self._file.write(f"ACTIVE_PROFILE: '{active.name}'\n")
        self._file.write(f"    COUNTERS: \"{self._format_counters(active)}\"\n")
        self._file.write(f"    HISTORY:  \"{self._format_history(active)}\"\n\n")
        for profile in profiles:
            if profile.name == active.name:
                continue
            self._file.write(f"PROFILE_NAME: '{profile.name}'\n")
            self._file.write(f"    COUNTERS: \"{self._format_counters(profile)}\"\n")
            self._file.write(f"    HISTORY:  \"{self._format_history(profile)}\"\n\n")
        self._file.write('------------------------------\n\n')
        self._file.flush()
        self._events_started = False
        self.close()

    def _ensure_events(self) -> None:
        """ Гарантирует наличие секции EVENTS. """
        if not self._events_started:
            self._file.write('EVENTS:\n')
            self._events_started = True

    @staticmethod
    def _format_counters(profile: Profile) -> str:
        counters = profile.counters.as_dict()
        parts = [f"{state.name}: {counters[state.cls_id]}" for state in profile.states.values()]
        return ', '.join(parts)

    @staticmethod
    def _format_history(profile: Profile) -> str:
        names = [state.name for state in profile.history]
        return ', '.join(names) + (', ' if names else '')
