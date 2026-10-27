from __future__ import annotations

__all__ = ['FsmConfig']

from typing import Any, Optional

from ..models.enums import ProfileSwitcherStrategies
from .history_writer_config import HistoryWriterConfig
from .profile_config import ProfileConfig, ProfileConfigTuple
from .state_config import StateConfig, StateConfigDict


class FsmConfig:
    """
        Итоговая (проверенная) конфигурация машины состояний.
        Создаётся FsmConfigBuilder.build() или парсерами конфигураций; вручную создавать не требуется.
        Неизменяема после создания.
    """

    __slots__ = ("_enable", "_profiles", "_def_profile", "_switcher_strategy", "_meta",
                 "_raw_history_writer", "_stable_history_writer")

    def __init__(
            self,
            *,
            enable: bool,
            profiles: ProfileConfigTuple,
            def_profile: Optional[str],
            switcher_strategy: ProfileSwitcherStrategies = ProfileSwitcherStrategies.SINGLE,
            meta: Optional[dict[str, Any]] = None,
            raw_history_writer: Optional[HistoryWriterConfig] = None,
            stable_history_writer: Optional[HistoryWriterConfig] = None,
    ) -> None:
        self._enable: bool = enable
        self._profiles: ProfileConfigTuple = tuple(profiles)
        self._def_profile: Optional[str] = def_profile
        self._switcher_strategy: ProfileSwitcherStrategies = switcher_strategy
        self._meta: dict[str, Any] = dict(meta or {})
        self._raw_history_writer: HistoryWriterConfig = raw_history_writer or HistoryWriterConfig.disabled()
        self._stable_history_writer: HistoryWriterConfig = stable_history_writer or HistoryWriterConfig.disabled()
        if self._enable and not self._profiles:
            raise ValueError("[FsmConfig] Enabled config must contain at least one profile")
        if self._enable and self.get_profile(def_profile) is None:
            raise ValueError(f"[FsmConfig] Default profile {def_profile!r} not found among profiles")

    @classmethod
    def create_disabled(cls, meta: Optional[dict[str, Any]] = None) -> FsmConfig:
        """ Конфигурация выключенной машины состояний (без профилей). """
        return cls(enable=False, profiles=(), def_profile=None, meta=meta)

    @property
    def enable(self) -> bool:
        """ Включена ли машина состояний. """
        return self._enable

    @property
    def profile_configs(self) -> ProfileConfigTuple:
        """ Конфигурации всех профилей. """
        return self._profiles

    @property
    def def_profile(self) -> Optional[str]:
        """ Имя профиля по умолчанию. """
        return self._def_profile

    @property
    def switcher_strategy(self) -> ProfileSwitcherStrategies:
        """ Стратегия переключения профилей. """
        return self._switcher_strategy

    @property
    def profile_ids_map(self) -> dict[str, tuple[int, ...]]:
        """ Соответствие имя профиля → внешние id. """
        return {p.name: p.mapped_ids for p in self._profiles}

    @property
    def state_configs(self) -> StateConfigDict:
        """
            Объединённая карта состояний всех профилей.
            При совпадении cls_id приоритет у профиля по умолчанию.
        """
        result: StateConfigDict = {}
        for profile in self._profiles:
            if profile.name != self._def_profile:
                result.update(profile.states)
        default_profile = self.get_profile(self._def_profile)
        if default_profile is not None:
            result.update(default_profile.states)
        return result

    @property
    def meta(self) -> dict[str, Any]:
        """ Дополнительные (нераспознанные) параметры исходной конфигурации. """
        return self._meta

    @property
    def raw_history_writer(self) -> HistoryWriterConfig:
        return self._raw_history_writer

    @property
    def stable_history_writer(self) -> HistoryWriterConfig:
        return self._stable_history_writer

    def get_profile(self, name: Optional[str]) -> Optional[ProfileConfig]:
        """ Возвращает конфигурацию профиля по имени. """
        return next((p for p in self._profiles if p.name == name), None)

    def get_state_by_cls_id(self, cls_id: int) -> Optional[StateConfig]:
        """ Возвращает конфигурацию состояния по cls_id (см. state_configs). """
        return self.state_configs.get(cls_id)

    def get_state_threshold_by_cls_id(self, cls_id: int) -> Optional[float]:
        """ Возвращает индивидуальный порог уверенности состояния или None. """
        state = self.get_state_by_cls_id(cls_id)
        return state.threshold if state else None

    def to_dict(self) -> dict[str, Any]:
        """ Сериализует конфигурацию в словарь. """
        return {
            "enable": self._enable,
            "switcher_strategy": self._switcher_strategy.name,
            "def_profile": self._def_profile,
            "profiles": [p.to_dict() for p in self._profiles],
        }
