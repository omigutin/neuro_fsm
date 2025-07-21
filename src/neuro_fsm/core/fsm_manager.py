__all__ = ['FsmManager']

from typing import Optional, Any

from ..configs import FsmConfig
from src.neuro_fsm.parsers.parser_factory import ParserFactory
from ..models import StateTuple
from .fsm import Fsm


class FsmManager:
    """
        Менеджер конфигураций для машин состояний.
        Отвечает за:
        - загрузку и парсинг конфигурации;
        - создание экземпляров StateMachine с актуальной конфигурацией.
    """

    def __init__(self, raw_config: Optional[Any] = None) -> None:
        """
            Инициализация менеджера. Может сразу принять конфигурацию.
            Args:
                raw_config: Сырые настройки (dict, объект, путь и т.д.)
        """
        self._config: Optional[FsmConfig] = self._parse_raw_config(raw_config) if raw_config else None
        self._state_machines: list[Fsm] = []

    def set_config(self, raw_config: Optional[Any] = None) -> None:
        """ Устанавливает новую конфигурацию для последующих StateMachine. """
        self._config = self._parse_raw_config(raw_config) if raw_config else self._config
        if self._config is None:
            raise ValueError(f"Config for state machine must be defined.")

    def create_state_machine(self, raw_config: Optional[Any] = None) -> Fsm:
        """
            Создаёт новую машину состояний и возвращает её.
            Args:
                raw_config: Необязательная индивидуальная конфигурация.
            Returns:
                Fsm: новая машина состояний.
        """
        self.set_config(raw_config)
        machine = Fsm(self._config)
        self._state_machines.append(machine)
        return machine

    @property
    def enable(self) -> bool:
        """ True, если включено использование машины состояний. """
        return self._config.enable if self._config else False

    @property
    def states(self) -> StateTuple:
        """ Список всех возможных состояний (StateClass). """
        return self._config.states

    @staticmethod
    def _parse_raw_config(raw_config: Any) -> FsmConfig:
        """
            Парсит произвольный формат конфигурации в StateMachineConfig.
            Args:
                raw_config: Сырые данные.
            Returns:
                FsmConfig: объект конфигурации.
        """
        return ParserFactory.parse(raw_config)

    def destroy(self) -> None:
        """ Сбрасывает конфигурацию и список созданных машин. """
        self._config = None
        self._state_machines.clear()

    # def is_reset_trigger(self, state: Optional[StateOrIdType] = None) -> bool:
    #     """ Проверяет, является ли состояние триггером для скидывания """
    #     state = self._get_state(state)
    #     return state.reset_trigger if state else self._cur_state.reset_trigger
    #
    # def is_break_trigger(self, state: Optional[StateOrIdType] = None) -> bool:
    #     """ Проверяет, является ли состояние триггером для прерывания обработки """
    #     state = self._get_state(state)
    #     return state.break_trigger if state else self._cur_state.break_trigger
    #
    # def register_state(self, state: StateOrIdType) -> StateMeta:
    #     """ Устанавливаем состояние и прибавляем счётчик этого состояния. Возвращает текущее состояние. """
    #     state = self._get_state(state)
    #     if state:
    #         self._counters.update(state)
    #         self._cur_state = state
    #         return self._cur_state
    #
    # def is_stable(self, state: Optional[StateMeta] = None) -> bool:
    #     """ Проверяет, является ли состояние стабильным """
    #     state = state or self._cur_state
    #     count = self._counters.get(state)
    #     return state.stable_min_lim == count
    #
    # def reset_resettable_states(self, reset_cur_state: bool = True) -> None:
    #     """ Скидывает все скидываемые счётчики состояний """
    #     if reset_cur_state:
    #         self._counters.reset_resettable()
    #     else:
    #         self._counters.reset_resettable_except(self.cur_state)
    #
    # def reset_all_states(self, reset_cur_state: bool = True) -> None:
    #     """ Скидывает все счётчики состояний """
    #     if reset_cur_state:
    #         self._counters.reset_all()
    #     else:
    #         self._counters.reset_all_except(self.cur_state)
    #
    # def is_correct_history(self) -> bool:
    #     return self._history.is_validity()
    #
    # def add_to_history(self, state: Optional[StateMeta] = None) -> None:
    #     """ Добавляет состояние в историю и скидывает его счётчик, если статус был добавлен """
    #     self._history.create_state_machine(state or self._cur_state)
    #
    # def clear_history(self) -> None:
    #     self._history.clear()
    #     self.add_to_history(self._cur_state)
