from __future__ import annotations

__all__ = ['Fsm']

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from ..configs import FsmConfig
from ..history_writer import StableHistoryWriter, RawHistoryWriter
from ..models.result import FsmResult
from .active_profile_view import ActiveProfileView
from .history import RawStateHistory
from .profiles.profile import Profile
from .profiles.profile_manager import ProfileManager
from .states import State


class Fsm:
    """
        Машина состояний для одного потока предсказаний (например, одной рабочей зоны).
        На каждом шаге process_state(cls_id):
            1. Входное состояние передаётся всем профилям (у каждого свои счётчики и история);
            2. Состояния-триггеры сброса сбрасывают счётчики сбрасываемых состояний;
            3. Состояние, счётчик которого достиг stable_min_lim, попадает в историю стабильных состояний,
               остальные счётчики сбрасываются;
            4. Если история активного профиля завершилась ожидаемой последовательностью — stage_done,
               и все профили сбрасываются к стартовому состоянию;
            5. Иначе профиль может смениться автоматически согласно стратегии.
        Неизвестный cls_id (или None) заменяется состоянием по умолчанию профиля.
    """

    def __init__(self, config: FsmConfig) -> None:
        self._enable: bool = config.enable
        self._meta: dict[str, Any] = config.meta
        self._result: Optional[FsmResult] = None
        self._step_index: int = 0
        self._raw_history = RawStateHistory()
        self._profile_manager: Optional[ProfileManager] = None
        self._profile_view: Optional[ActiveProfileView] = None
        self._raw_history_writer: Optional[RawHistoryWriter] = None
        self._stable_history_writer: Optional[StableHistoryWriter] = None
        self._last_profile_name: str = ""
        if not self._enable:
            return

        if config.def_profile is None:
            raise ValueError("[Fsm] Enabled config must define default profile")
        self._profile_manager = ProfileManager(
            profile_configs=config.profile_configs,
            switcher_strategy=config.switcher_strategy,
            def_profile=config.def_profile,
        )
        self._profile_view = ActiveProfileView(self._profile_manager)
        self._last_profile_name = self._profile_manager.active_profile.name

        if config.raw_history_writer.enable:
            self._raw_history_writer = RawHistoryWriter(config.raw_history_writer)
        if config.stable_history_writer.enable:
            self._stable_history_writer = StableHistoryWriter(config.stable_history_writer)
            self._stable_history_writer.write_configs(config.to_dict())
            self._stable_history_writer.write_profile_configs(self._profile_manager.profiles)

    # ---------------- свойства ----------------

    @property
    def enable(self) -> bool:
        """ Включена ли машина состояний. """
        return self._enable

    @property
    def meta(self) -> dict[str, Any]:
        """ Дополнительные параметры конфигурации. """
        return self._meta

    @property
    def profile(self) -> ActiveProfileView:
        """ Read-only представление активного профиля. """
        return self._view()

    @property
    def profile_names(self) -> tuple[str, ...]:
        """ Имена всех профилей. """
        return tuple(self._manager().profiles.keys())

    @property
    def result(self) -> Optional[FsmResult]:
        """ Последний результат или None, если шагов ещё не было (или после reset). """
        return self._result

    @property
    def step_index(self) -> int:
        """ Количество обработанных шагов с момента создания или сброса. """
        return self._step_index

    # ---------------- управление профилями ----------------

    def switch_profile_by_pid(self, pid: Optional[int]) -> bool:
        """
            Делает активным профиль по внешнему id (например, id продукции).
            Незнакомый id или None — профиль по умолчанию.
            Returns: True, если активный профиль сменился.
        """
        manager = self._manager()
        changed = manager.switch_profile_by_pid(pid)
        if changed:
            self._write_action(manager.active_profile.cur_state, "profile_switched_by_pid", manager.active_profile)
        return changed

    def switch_profile_by_name(self, profile_name: Union[str, Enum]) -> bool:
        """
            Делает активным профиль по имени (без учёта регистра).
            Returns: True, если активный профиль сменился.
        """
        manager = self._manager()
        changed = manager.switch_profile_by_name(profile_name)
        if changed:
            self._write_action(manager.active_profile.cur_state, "profile_switched_by_name", manager.active_profile)
        return changed

    # ---------------- обработка ----------------

    def process_state(self, cls_id: Optional[int]) -> FsmResult:
        """
            Обрабатывает одно предсказание нейросети.
            Args:
                cls_id: идентификатор класса; None или неизвестный — состояние по умолчанию.
            Returns:
                FsmResult: результат шага. Для выключенной FSM — пустой результат.
        """
        if not self._enable:
            return FsmResult.create_empty()

        manager = self._manager()
        self._step_index += 1
        prev_state = self._result.state if self._result else None

        manager.register_state(cls_id)
        active = manager.active_profile
        cur_state = active.cur_state

        if self._raw_history_writer is not None:
            self._raw_history_writer.write(str(cls_id))
        self._write_state_change(prev_state, cur_state, active)
        self._raw_history.add(cur_state)

        manager.reset_by_trigger()
        for profile in manager.commit_stable_states():
            self._write_action(profile.cur_state, "add_state_to_history", profile)
        stable = active.is_state_stable()

        stage_done = active.is_expected_seq_valid()
        if not stage_done and manager.update_active_profile():
            active = manager.active_profile
            self._write_action(active.cur_state, "profile_changed", active)
            # При BY_MATCH новый профиль выбран именно потому, что завершил последовательность
            stage_done = active.is_expected_seq_valid()

        counters = active.get_counters()
        history = active.get_history()
        if stage_done:
            self._write_action(active.cur_state, "EXPECTED_SEQ_DONE", active)
            if self._stable_history_writer is not None:
                self._stable_history_writer.write_runtime(manager.profiles, active)
            manager.reset_all_to_init()

        profile_changed = active.name != self._last_profile_name
        result = FsmResult(
            active_profile=active.name,
            prev_profile=self._last_profile_name if profile_changed else None,
            state=active.cur_state,
            resetter=active.cur_state.is_resetter,
            breaker=active.cur_state.is_breaker,
            stable=stable,
            stage_done=stage_done,
            profile_changed=profile_changed,
            counters=counters,
            history=history,
            step_index=self._step_index,
            timestamp=datetime.now(),
        )
        self._last_profile_name = active.name
        self._result = result
        return result

    def reset(self) -> None:
        """ Сбрасывает счётчики и историю всех профилей, последний результат и номер шага. Профиль не меняется. """
        self._result = None
        self._step_index = 0
        self._raw_history.clear()
        if self._profile_manager is not None:
            self._profile_manager.reset_all_to_init()
            self._last_profile_name = self._profile_manager.active_profile.name

    def close(self) -> None:
        """ Закрывает файлы писателей истории. """
        for writer in (self._raw_history_writer, self._stable_history_writer):
            if writer is not None:
                writer.close()

    # ---------------- служебное ----------------

    def _manager(self) -> ProfileManager:
        if self._profile_manager is None:
            raise RuntimeError("FSM is disabled: profiles are not available")
        return self._profile_manager

    def _view(self) -> ActiveProfileView:
        if self._profile_view is None:
            raise RuntimeError("FSM is disabled: profiles are not available")
        return self._profile_view

    def _write_state_change(self, prev_state: Optional[State], cur_state: State, active: Profile) -> None:
        """ Пишет в стабильную историю смену входного состояния. """
        if self._stable_history_writer is None:
            return
        if prev_state is not None and prev_state.cls_id != cur_state.cls_id:
            self._stable_history_writer.write_action(
                cur_state=prev_state,
                count=active.get_counter_by_cls_id(prev_state.cls_id),
                action="state_changed",
                profile=active,
            )
        if prev_state is None or prev_state.cls_id != cur_state.cls_id:
            self._stable_history_writer.write_state(cur_state)

    def _write_action(self, state: State, action: str, profile: Profile) -> None:
        if self._stable_history_writer is not None:
            self._stable_history_writer.write_action(
                cur_state=state, count=profile.get_counter_by_cls_id(state.cls_id), action=action, profile=profile
            )

    def __repr__(self) -> str:
        profile = self._profile_manager.active_profile.name if self._profile_manager else None
        return f"<Fsm enable={self._enable} profile={profile} step={self._step_index}>"
