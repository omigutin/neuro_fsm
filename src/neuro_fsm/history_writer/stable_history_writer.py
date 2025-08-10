__all__ = ['StableHistoryWriter']

from datetime import datetime
from typing import Any, Dict

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
        """Записывает общие настройки FSM в упрощённом и читабельном виде."""
        self._file.write("FSM_CONFIGURATION:\n")
        self._file.write(f"\tenable: {record.get('enable')}\n")
        self._file.write("\tstate_configs:\n")
        for cls_id, cfg in record.get("state_configs", {}).items():
            cfg_repr = dict(cfg)
            cfg_repr.pop("cls_id", None)
            self._file.write(f"\t\t{cls_id}: {cfg_repr}\n")
        if "switcher_strategy" in record:
            self._file.write(f"\tswitcher_strategy: {record['switcher_strategy']}\n")
        if "def_profile" in record:
            self._file.write(f"\tdef_profile: {record['def_profile']}\n\n")
        self._file.flush()

    def write_profile_configs(self, profiles: ProfileDict) -> None:
        """Выводит конфигурацию всех профилей в валидном YAML-формате."""

        def yaml_str(s: str) -> str:
            # Двойные кавычки, экранируем внутренние
            return '"' + s.replace('"', '\\"') + '"'
        def yaml_bool(v: bool) -> str:
            return "true" if bool(v) else "false"

        def yaml_none(v) -> str:
            return "null" if v is None else v  # возвращаем исходное (числа/строки обрабатываем выше)

        def fmt_state(state: 'State') -> str:
            # Собираем словарь полей как в твоём примере
            cls_id = getattr(state, "cls_id")
            name = yaml_str(getattr(state, "name"))
            full_name = yaml_str(getattr(state, "full_name", "") or "")
            is_fiction = yaml_bool(getattr(state, "is_fiction", getattr(state, "fiction", False)))
            alias_of = yaml_none(getattr(state, "alias_of", None))
            stable_min_lim = getattr(state, "stable_min_lim")
            is_resettable = yaml_bool(getattr(state, "is_resettable", getattr(state, "resettable", False)))
            is_resetter = yaml_bool(getattr(state, "is_resetter", getattr(state, "reset_trigger", False)))
            is_breaker = yaml_bool(getattr(state, "is_breaker", getattr(state, "break_trigger", False)))
            threshold = getattr(state, "threshold", 0.0) or 0.0

            # В одну строку, в фигурных скобках
            return (
                f"{{cls_id: {cls_id}, name: {name}, full_name: {full_name}, "
                f"is_fiction: {is_fiction}, alias_of: {alias_of}, "
                f"stable_min_lim: {stable_min_lim}, is_resettable: {is_resettable}, "
                f"is_resetter: {is_resetter}, is_breaker: {is_breaker}, threshold: {threshold}}}"
            )

        def fmt_state_names(states: tuple['State', ...]) -> str:
            # ["EMPTY", "UNKNOWN"]
            inside = ", ".join(yaml_str(s.name) for s in states)
            return f"[{inside}]"

        def fmt_sequences(seqs: tuple[tuple['State', ...], ...]) -> str:
            # - ["EMPTY", "FULL", "EMPTY"]
            lines = []
            for seq in seqs:
                items = ", ".join(yaml_str(s.name) for s in seq)
                lines.append(f"      - [{items}]")
            return "\n".join(lines)

        w = self._file.write
        w("PROFILES_CONFIGURATION:\n")

        for profile in profiles.values():
            w(f"  - profile_name: {profile.name}\n")
            w("    states:\n")
            for st in profile.states.values():
                w(f"      - {fmt_state(st)}\n")
            w(f"    init_states: {fmt_state_names(profile.init_states)}\n")
            w(f"    default_states: {fmt_state_names(profile.default_states)}\n")
            w("    expected_sequences:\n")
            w(fmt_sequences(profile.history.expected_sequences) + "\n\n")
        w("==============================\n\n")
        self._file.flush()

    def write_state(self, state: State) -> None:
        """Записывает событие состояния в YAML-формате (без библиотеки)."""
        self.open()
        self._ensure_events()
        timestamp = datetime.now().strftime('%H:%M:%S')
        self._file.write(f"\t- state: \"{state.name} [{timestamp}]\"\n")
        self._file.flush()

    def write_action(self, action: str, active_profile: Profile) -> None:
        """Записывает событие действия в YAML-формате (без библиотеки)."""
        self.open()
        self._ensure_events()
        self._file.write(f"\t- action:\n")
        self._file.write(f"    {action}:\n")
        self._file.write(f"      active_profile: {active_profile.name}\n")
        self._file.flush()

    def write_runtime(self, profiles: ProfileDict, active_profile: Profile) -> None:
        """Фиксирует текущее состояние всех профилей в чистом YAML."""

        def yaml_str(s: str) -> str:
            return '"' + s.replace('"', '\\"') + '"'

        def fmt_counters(p: Profile) -> dict[str, int]:
            return {
                state.name: p.counters.get(state.cls_id)
                for state in p.states.values()
            }

        def fmt_history(p: Profile) -> str:
            return f"[{', '.join(yaml_str(s.name) for s in p.history.records)}]"

        w = self._file.write
        w("\n------------------------------\nRUNTIME:\n")
        w(f"  active_profile: {active_profile.name}\n")
        w(f"  counters: {fmt_counters(active_profile)}\n")
        w(f"  history: {fmt_history(active_profile)}\n\n")
        w("  profiles:\n")
        for profile in profiles.values():
            if profile.name == active_profile.name:
                continue
            w(f"    - profile_name: {profile.name}\n")
            w(f"      counters: {fmt_counters(profile)}\n")
            w(f"      history: {fmt_history(profile)}\n")
        w("------------------------------\n")
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
