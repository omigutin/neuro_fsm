from __future__ import annotations

__all__ = ['Fsm']

from typing import Optional, Any

from ..configs import FsmConfig
from ..models import StateMachineResult
from .profiles.profile_manager import StateProfilesManager
from .history import RawStateHistory
from .states import State, StateFactory, StateDict
from .profiles.profile import Profile


class Fsm:
    """ Машина состояний, управляющая историей и счётчиками состояний """

    def __init__(self, config: FsmConfig) -> None:
        self._enable: bool = config.enable
        self._states: StateDict = StateFactory.build(config.states)
        self._cur_state: Optional[State] = None
        self._meta: dict[str, Any] = config.meta
        self._raw_history = RawStateHistory()
        self._profile_manager: StateProfilesManager = StateProfilesManager(
            config.profile_configs,
            config.switcher_strategy,
            config.def_profile,
            self._states
        )
        self._result: Optional[StateMachineResult] = None

    @property
    def active_profile(self) -> Profile:
        return self._profile_manager.active_profile

    # @property
    # def history(self):
    #     return self.active_profile.history

    @property
    def cur_state(self) -> Optional[State]:
        return self._cur_state

    @property
    def result(self) -> Optional[StateMachineResult]:
        return self._result

    def process_state(self, cls_id: int) -> StateMachineResult:
        """
            Обрабатывает новое состояние машины состояний.
            Этапы обработки:
            1. Получение объекта состояния (`State`) по его идентификатору.
            2. Если состояние является триггером сброса — сбрасываются счётчики других состояний.
            3. Если состояние является триггером прерывания — возвращается флаг прерывания обработки.
            4. Если состояние стабильно — записывается в историю, остальные счётчики сбрасываются.
            5. Если история соответствует ожидаемой последовательности — подготавливается флаг события и
               сбрасываются все состояния.
            Args:
                cls_id (StateOrIdType): Идентификатор или объект состояния, полученный от нейросети.
            Returns:
                tuple[bool, bool]:
                    - Первый элемент — `True`, если сработала последовательность и нужно отправить событие.
                    - Второй элемент — `True`, если необходимо прервать обработку (например, отсутствует объект).
        """
        self._cur_state = self._get_state(cls_id)
        self._add_to_raw_history(self._cur_state)
        self._handle_reset_trigger()
        break_search = self._handle_break_trigger()
        self._handle_stable_state()
        stage_done = self._check_profile_completion()

        self._result = StateMachineResult(
            stage_done=stage_done,
            state=self.active_profile.get_state(cls_id),
            break_search=break_search,
            stable_state=self.active_profile.is_stable(),
            counters=self.active_profile._counters.copy(),
            active_profile=self.active_profile.name if self.active_profile else None,
        )
        return self._result

    def _get_state(self, cls_id: int) -> State:
        return self._states[cls_id]

    def _handle_reset_trigger(self) -> None:
        if self.active_profile.is_reset_trigger(self._cur_state.cls_id):
            self.active_profile.reset_resettable_except(self.cur_state.cls_id)

    def _handle_break_trigger(self) -> bool:
        return self.active_profile.is_break_trigger(self._cur_state.cls_id)

    def _handle_stable_state(self) -> None:
        if self.active_profile.is_stable(self._cur_state.cls_id):
            self.active_profile.update(self._cur_state.cls_id)
            self.active_profile.reset_all_states()

    def _check_profile_completion(self) -> bool:
        if self.active_profile.is_expected_seq_valid():
            self.active_profile.reset_all_states(self.cur_state.cls_id)
            return True
        return False

    def _add_to_raw_history(self, state:  State) -> None:
        """ Добавляет состояние в историю и скидывает его счётчик, если статус был добавлен """
        self._raw_history.add(state)
