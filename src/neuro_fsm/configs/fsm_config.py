from __future__ import annotations

__all__ = ['FsmConfig']

from typing import Optional, Any

from .history_writer_config import HistoryWriterConfig
from .profile_config import ProfileConfigTuple
from .state_config import StateConfig, StateConfigDict
from ..models.enums import ProfileSwitcherStrategies, ProfileNames


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
            state_configs: StateConfigDict,
            profiles: ProfileConfigTuple,
            switcher_strategy: Optional[ProfileSwitcherStrategies],
            def_profile: str,
            profile_ids_map,
            meta: dict[str, Any],
            raw_history_writer: HistoryWriterConfig,
            stable_history_writer: HistoryWriterConfig
    ) -> None:
        self._enable: bool = enable
        self._state_configs: StateConfigDict = state_configs
        self._profile_configs: ProfileConfigTuple = profiles
        self._switcher_strategy: Optional[ProfileSwitcherStrategies] = switcher_strategy
        self._def_profile: str = def_profile
        self._profile_ids_map = profile_ids_map
        self._meta: dict[str, Any] = meta
        self._raw_history_writer: HistoryWriterConfig = raw_history_writer
        self._stable_history_writer: HistoryWriterConfig = stable_history_writer

    @property
    def enable(self) -> bool:
        """ Включена ли машина состояний. """
        return self._enable

    @property
    def state_configs(self) -> StateConfigDict:
        """ Словарь доступных состояний. """
        return self._state_configs

    @property
    def profile_configs(self) -> ProfileConfigTuple:
        return self._profile_configs

    @property
    def switcher_strategy(self) -> ProfileSwitcherStrategies:
        return self._switcher_strategy if self._switcher_strategy else ProfileSwitcherStrategies.SINGLE

    @property
    def def_profile(self) -> str:
        return self._def_profile if self._def_profile else ProfileNames.SINGLE

    @property
    def profile_ids_map(self):
        return self._profile_ids_map

    @property
    def meta(self) -> dict[str, Any]:
        return self._meta

    @property
    def raw_history_writer(self) -> HistoryWriterConfig:
        return self._raw_history_writer

    @property
    def stable_history_writer(self) -> HistoryWriterConfig:
        return self._stable_history_writer

    def get_state_by_cls_id(self, cls_id: int) -> Optional[StateConfig]:
        return self.state_configs.get(cls_id) if self.state_configs else None

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

    def to_dict(self) -> dict:
        return {
            "enable": self._enable,
            "state_configs": {k: state_config.to_dict() for k, state_config in self._state_configs.items()},
            "profile_configs": [profile_config.to_dict() for profile_config in self._profile_configs],
            "switcher_strategy": self._switcher_strategy.name,
            "def_profile": self._def_profile,
        }
