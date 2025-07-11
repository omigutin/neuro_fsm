from __future__ import annotations

__all__ = ['StateMachine']

from typing import Optional, Any

from ..config_profiles import StateMachineConfig
from ..config_profiles.parsers.parser_factory import ParserFactory
from ..config_profiles.state_profiles.profiles_manager import StateProfilesManager
from ..history import RawStateHistory
from ..models import StateMeta, StatesTuple, StateMachineResult, StateOrIdType


class StateMachine:
    """ Машина состояний, управляющая историей и счётчиками состояний """

    def __init__(self, config: StateMachineConfig) -> None:
        self._enable: bool = config.enable
        self._states: StatesTuple = ()
        self._meta: dict[str, Any] = config.meta

        self._raw_history = RawStateHistory(config.)
        self._profile_manager: StateProfilesManager = StateProfilesManager(config.profiles, config.switcher_strategy)
        self._cur_state: Optional[StateMeta] = None
        self._result: Optional[StateMachineResult] = None

    @property
    def init_states(self) -> StatesTuple:
        return self._profile_manager.active_profile.init_states

    @property
    def default_states(self) -> StatesTuple:
        return self._profile_manager.active_profile.default_states

    @property
    def cur_state(self) -> Optional[StateMeta]:
        return self._cur_state if self._cur_state else None

    @property
    def result(self) -> Optional[StateMachineResult]:
        return self._result

    @staticmethod
    def parse_raw_config(raw_config: Any) -> StateMachineConfig:
        """ Запускает фабрику по парсингу любого типа настроек и приводит их к собственному виду """
        try:
            config = ParserFactory.parse(raw_config)
        except Exception as e:
            raise e
        else:
            return config

    def process_state(self, cls_id: StateOrIdType) -> StateMachineResult:
        """
            Обрабатывает новое состояние машины состояний.
            Этапы обработки:
            1. Получение объекта состояния (`StateMeta`) по его идентификатору.
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
        cur_state = self._get_state(cls_id)
        self._handle_reset_trigger(cur_state)
        break_search = self._handle_break_trigger(cur_state)
        self._handle_stable_state(cur_state)
        stage_done = self._check_profile_completion()

        self._result = StateMachineResult(
            stage_done=stage_done,
            cur_state=cur_state,
            break_search=break_search,
            stable_state=self._cur_state if self.is_stable() else None,
            counters=self._counters.copy(),
            active_profile=self._active_profile.profile.name if self._active_profile else None,
        )
        return self._result

    def _handle_reset_trigger(self, state: StateMeta) -> None:
        if self.is_reset_trigger(state):
            self.reset_resettable_states(reset_cur_state=False)

    def _handle_break_trigger(self, state: StateMeta) -> bool:
        return self.is_break_trigger(state)

    def _handle_stable_state(self, state: StateMeta) -> None:
        if self.is_stable(state):
            self.add_to_history(state)
            self.reset_all_states(reset_cur_state=False)

    def _check_profile_completion(self) -> bool:
        if self.is_correct_history():
            self.reset_all_states()
            self.clear_history()
            return True
        return False

    def is_reset_trigger(self, state: Optional[StateOrIdType] = None) -> bool:
        """ Проверяет, является ли состояние триггером для скидывания """
        state = self._get_state(state)
        return state.reset_trigger if state else self._cur_state.reset_trigger

    def is_break_trigger(self, state: Optional[StateOrIdType] = None) -> bool:
        """ Проверяет, является ли состояние триггером для прерывания обработки """
        state = self._get_state(state)
        return state.break_trigger if state else self._cur_state.break_trigger

    def set_cur_state(self, state: StateOrIdType):
        """ Устанавливаем состояние и прибавляем счётчик этого состояния """
        state = self._get_state(state)
        if state:
            self._counters.update(state)
            self._cur_state = state

    def is_stable(self, state: Optional[StateMeta] = None) -> bool:
        """ Проверяет, является ли состояние стабильным """
        state = state or self._cur_state
        count = self._counters.get(state)
        return state.stable_min_lim == count

    def reset_resettable_states(self, reset_cur_state: bool = True) -> None:
        """ Скидывает все скидываемые счётчики состояний """
        if reset_cur_state:
            self._counters.reset_resettable()
        else:
            self._counters.reset_resettable_except(self.cur_state)

    def reset_all_states(self, reset_cur_state: bool = True) -> None:
        """ Скидывает все счётчики состояний """
        if reset_cur_state:
            self._counters.reset_all()
        else:
            self._counters.reset_all_except(self.cur_state)

    def is_correct_history(self) -> bool:
        return self._history.is_validity()

    def add_to_history(self, state: Optional[StateMeta] = None) -> None:
        """ Добавляет состояние в историю и скидывает его счётчик, если статус был добавлен """
        self._history.create_state_machine(state or self._cur_state)

    def clear_history(self) -> None:
        self._history.clear()
        self.add_to_history(self._cur_state)

    def destroy(self) -> None:
        self._config = None
        self._counters = {}
        self._cur_state = None
        self._history = None

    def _get_state(self, state: StateOrIdType) -> StateMeta:
        """ Преобразует cls_id → StateMeta или валидирует StateMeta. """
        if isinstance(state, int):
            resolved = self._states.get(state)
            if not resolved:
                raise ValueError(f"StateMeta with cls_id={state} not found in StateMachine")
            return resolved
        elif isinstance(state, StateMeta):
            return state
        raise TypeError(f"Expected int or StateMeta, got {type(state)}")
