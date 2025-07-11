from __future__ import annotations

__all__ = ['StateMachineConfig']

from typing import Optional, Any

from .state_profiles import ProfileSwitcherStrategy
from .state_profiles.states_profile import StateProfileTuple
from ..models import State, StatesDict


class StateMachineConfig:
    """
        Конфигурация и состояние машины состояний.
        Используется как фасад над выбранным `StatesProfileConfig`, чтобы обеспечить удобный и единообразный доступ к:
        - списку доступных состояний,
        - начальному состоянию,
        - состояниям по умолчанию,
        - ожидаемым последовательностям.
    """

    def __init__(
            self,
            enable: bool,
            switcher_strategy: Optional[ProfileSwitcherStrategy],
            states: StatesDict,
            profiles: StateProfileTuple,
            meta: dict[str, Any]
    ) -> None:
        self._enable: bool = enable
        self._states: StatesDict = states
        self._profiles: StateProfileTuple = profiles
        self._switcher_strategy: Optional[ProfileSwitcherStrategy] = switcher_strategy
        self._meta: dict[str, Any] = meta

    @property
    def enable(self) -> bool:
        """ Включена ли машина состояний. """
        return self._enable

    @property
    def states(self) -> StatesDict:
        """ Словарь доступных состояний. """
        return self._states

    @property
    def profiles(self) -> StateProfileTuple:
        return self._profiles

    @property
    def switcher_strategy(self) -> ProfileSwitcherStrategy:
        return self._switcher_strategy if self._switcher_strategy else ProfileSwitcherStrategy.MIXED

    @property
    def meta(self) -> dict[str, Any]:
        return self._meta

    def get_state_by_cls_id(self, cls_id: int) -> Optional[State]:
        return self.states.get(cls_id) if self.states else None

    def get_state_threshold_by_cls_id(self, cls_id: int) -> Optional[float]:
        """
            Возвращает индивидуальный порог уверенности для указанного состояния.
            Args:
                cls_id (int): Числовой ID класса состояния.
            Returns:
                Optional[float]: Порог уверенности или None.
        """
        state = self.get_state_by_cls_id(cls_id)
        return state.threshold if state else None

    def destroy(self) -> None:
        """
            Полностью сбрасывает текущую конфигурацию.
            Используется при завершении работы или полной переинициализации.
        """
        self._enable = False
        self._profiles = None
        self._meta = None
