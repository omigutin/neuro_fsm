from __future__ import annotations

__all__ = ['FsmConfig']

from typing import Optional, Any

from ..core.profiles import ProfileSwitcherStrategies, ProfileNames
from .profile_config import ProfileConfigTuple
from .state_config import StateConfig, StateConfigDict


class FsmConfig:
    """
        Конфигурация и состояние машины состояний.
        Используется как фасад над выбранным `StatesProfileConfig`, чтобы обеспечить удобный и единообразный доступ к:
        — списку доступных состояний,
        — начальному состоянию,
        — состояниям по умолчанию,
        — ожидаемым последовательностям.
    """

    def __init__(
            self,
            enable: bool,
            states: StateConfigDict,
            profiles: ProfileConfigTuple,
            switcher_strategy: Optional[ProfileSwitcherStrategies],
            def_profile: ProfileNames,
            meta: dict[str, Any]
    ) -> None:
        self._enable: bool = enable
        self._states: StateConfigDict = states
        self._profile_configs: ProfileConfigTuple = profiles
        self._switcher_strategy: Optional[ProfileSwitcherStrategies] = switcher_strategy
        self._def_profile: ProfileNames = def_profile
        self._meta: dict[str, Any] = meta

    @property
    def enable(self) -> bool:
        """ Включена ли машина состояний. """
        return self._enable

    @property
    def states(self) -> StateConfigDict:
        """ Словарь доступных состояний. """
        return self._states

    @property
    def profile_configs(self) -> ProfileConfigTuple:
        return self._profile_configs

    @property
    def switcher_strategy(self) -> ProfileSwitcherStrategies:
        return self._switcher_strategy if self._switcher_strategy else ProfileSwitcherStrategies.MIXED

    @property
    def meta(self) -> dict[str, Any]:
        return self._meta

    def get_state_by_cls_id(self, cls_id: int) -> Optional[StateConfig]:
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
            Используется при завершении работы или полной пере инициализации.
        """
        self._enable = False
        self._profile_configs = None
        self._meta = None
