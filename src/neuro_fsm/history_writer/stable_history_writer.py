__all__ = ['StableHistoryWriter']

from datetime import datetime
from typing import Any

from ..configs.history_writer_config import HistoryWriterConfig
from ..core.profiles.profile import Profile
from ..core.profiles.types import ProfileDict
from ..core.states import State
from .base_history_writer import BaseHistoryWriter


class StableHistoryWriter(BaseHistoryWriter):
    """ Писатель стабильной истории (события FSM) в YAML-подобном формате. """

    def __init__(self, config: HistoryWriterConfig) -> None:
        super().__init__(config, '.yaml')
        self._events_started = False

    def write_configs(self, record: dict[str, Any]) -> None:
        """ Записывает общие настройки FSM (enable, стратегия, профиль по умолчанию). """
        self._write(
            "FSM_CONFIGURATION:\n"
            f"  enable: {self._yaml_value(record.get('enable'))}\n"
            f"  switcher_strategy: {record.get('switcher_strategy')}\n"
            f"  def_profile: {record.get('def_profile')}\n\n"
        )

    def write_profile_configs(self, profiles: ProfileDict) -> None:
        """ Записывает конфигурацию всех рабочих профилей. """

        def fmt_state(state: State) -> str:
            return (
                f"{{cls_id: {state.cls_id}, name: {self._yaml_str(state.name)}, "
                f"full_name: {self._yaml_str(state.full_name)}, is_fiction: {self._yaml_value(state.is_fiction)}, "
                f"alias_of: {self._yaml_value(state.alias_of)}, "
                f"stable_min_lim: {self._yaml_value(state.stable_min_lim)}, "
                f"is_resettable: {self._yaml_value(state.is_resettable)}, "
                f"is_resetter: {self._yaml_value(state.is_resetter)}, "
                f"is_breaker: {self._yaml_value(state.is_breaker)}, threshold: {self._yaml_value(state.threshold)}}}"
            )

        def fmt_names(states: tuple[State, ...]) -> str:
            return "[" + ", ".join(self._yaml_str(s.name) for s in states) + "]"

        lines = ["PROFILES_CONFIGURATION:\n"]
        for profile in profiles.values():
            lines.append(f"  - profile_name: {profile.name}\n")
            lines.append("    states:\n")
            lines.extend(f"      - {fmt_state(st)}\n" for st in profile.states.values())
            lines.append(f"    init_states: {fmt_names(profile.init_states)}\n")
            lines.append(f"    default_states: {fmt_names(profile.default_states)}\n")
            lines.append("    expected_sequences:\n")
            lines.extend(f"      - {fmt_names(seq)}\n" for seq in profile.expected_sequences)
            lines.append("\n")
        lines.append("#" + "=" * 118 + "#\n")
        self._write("".join(lines))

    def write_state(self, state: State) -> None:
        """ Записывает смену входного состояния. """
        self._ensure_events()
        self._write(f"\t-  time: [{self._now()}], state: \"{state.name}\"\n")

    def write_action(self, cur_state: State, count: int, action: str, profile: Profile) -> None:
        """ Записывает событие (стабильность, смена профиля, срабатывание последовательности). """
        self._ensure_events()
        self._write(
            f"\t-  time: [{self._now()}], "
            f"state: \"{cur_state.name}\", profile: [{profile.name}], count: \"{count}\", action: \"{action}\"\n"
        )

    def write_runtime(self, profiles: ProfileDict, active_profile: Profile) -> None:
        """ Фиксирует снимок счётчиков и историй всех профилей. """

        def fmt_counters(p: Profile) -> dict[str, int]:
            return {state.name: count for state, count in p.get_counters().items()}

        def fmt_history(p: Profile) -> str:
            return f"[{', '.join(self._yaml_str(s.name) for s in p.get_history())}]"

        line = "#" + "-" * 118 + "#\n"
        lines = [
            "\n" + line,
            "RUNTIME:\n",
            "  active_profile:\n",
            f"    - profile_name: {active_profile.name}\n",
            f"      counters: {fmt_counters(active_profile)}\n",
            f"      history: {fmt_history(active_profile)}\n\n",
            "  profiles:\n",
        ]
        for profile in profiles.values():
            if profile.name == active_profile.name:
                continue
            lines.append(f"    - profile_name: {profile.name}\n")
            lines.append(f"      counters: {fmt_counters(profile)}\n")
            lines.append(f"      history: {fmt_history(profile)}\n")
        lines.append(line)
        self._write("".join(lines))
        self._events_started = False

    def _ensure_events(self) -> None:
        """ Гарантирует наличие секции EVENTS. """
        if not self._events_started:
            self._write('\nEVENTS:\n')
            self._events_started = True

    @staticmethod
    def _yaml_str(value: str) -> str:
        """ Строка в двойных кавычках с экранированием. """
        return '"' + value.replace('"', '\\"') + '"'

    @staticmethod
    def _yaml_value(value: object) -> str:
        """ Скаляр в YAML-представлении. """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%H:%M:%S')
