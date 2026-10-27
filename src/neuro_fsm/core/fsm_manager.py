from __future__ import annotations

__all__ = ['FsmManager']

from enum import Enum
from typing import Any, Iterator, Optional, Union

from ..configs import FsmConfig
from ..configs.state_config import StateConfigDict
from .fsm import Fsm


class FsmManager:
    """
        Создаёт машины состояний по общей конфигурации и управляет ими пакетно.
        Конфигурация принимается в любом поддерживаемом виде:
            - FsmConfig или FsmConfigBuilder (основной способ);
            - dict, класс или модуль с полями конфигурации (формат с профилями STATE_PROFILES
              или простой формат STATES / EXPECTED_SEQUENCES / INIT_STATE(S) / DEFAULT_STATE(S)).
        Ошибки конфигурации не глушатся: при некорректной конфигурации выбрасывается ValueError/TypeError.
    """

    def __init__(self, raw_config: Optional[Any] = None) -> None:
        self._config: Optional[FsmConfig] = None
        self._fsms: list[Fsm] = []
        if raw_config is not None:
            self.set_config(raw_config)

    @property
    def config(self) -> Optional[FsmConfig]:
        """ Текущая конфигурация или None. """
        return self._config

    @property
    def enable(self) -> bool:
        """ True, если конфигурация задана и FSM включена. """
        return self._config.enable if self._config else False

    @property
    def state_configs(self) -> StateConfigDict:
        """ Объединённая карта состояний текущей конфигурации. """
        return self._require_config().state_configs

    def set_config(self, raw_config: Any) -> None:
        """ Устанавливает конфигурацию для последующих create_fsm(). Уже созданные FSM не меняются. """
        self._config = self.parse_config(raw_config)

    def create_fsm(self, raw_config: Optional[Any] = None) -> Fsm:
        """
            Создаёт новую машину состояний.
            Args:
                raw_config: индивидуальная конфигурация этой FSM; None — общая конфигурация менеджера.
        """
        config = self.parse_config(raw_config) if raw_config is not None else self._require_config()
        fsm = Fsm(config)
        self._fsms.append(fsm)
        return fsm

    def switch_profile_by_pid(self, pid: Optional[int]) -> None:
        """ Меняет активный профиль по внешнему id у всех включённых FSM. """
        for fsm in self._enabled_fsms():
            fsm.switch_profile_by_pid(pid)

    def switch_profile_by_name(self, profile_name: Union[str, Enum]) -> None:
        """ Меняет активный профиль по имени у всех включённых FSM. """
        for fsm in self._enabled_fsms():
            fsm.switch_profile_by_name(profile_name)

    def reset_all(self) -> None:
        """ Сбрасывает все FSM. """
        for fsm in self._fsms:
            fsm.reset()

    def update_all(self, cls_id: Optional[int]) -> None:
        """ Передаёт одно состояние всем FSM. """
        for fsm in self._fsms:
            fsm.process_state(cls_id)

    def get_statuses(self) -> dict[int, str]:
        """ Имена активных профилей всех FSM по индексу ("" — FSM выключена). """
        return {i: fsm.profile.name if fsm.enable else "" for i, fsm in enumerate(self._fsms)}

    def destroy(self) -> None:
        """ Закрывает писателей истории, сбрасывает конфигурацию и список созданных машин. """
        for fsm in self._fsms:
            fsm.close()
        self._config = None
        self._fsms.clear()

    @staticmethod
    def parse_config(raw_config: Any) -> FsmConfig:
        """ Приводит конфигурацию любого поддерживаемого вида к FsmConfig. """
        from ..config_builder import FsmConfigBuilder
        from ..config_parser.parser_factory import ParserFactory

        if isinstance(raw_config, FsmConfig):
            return raw_config
        if isinstance(raw_config, FsmConfigBuilder):
            return raw_config.build()
        return ParserFactory.parse(raw_config)

    def _require_config(self) -> FsmConfig:
        if self._config is None:
            raise RuntimeError("FsmManager has no config. Pass it to the constructor or call set_config().")
        return self._config

    def _enabled_fsms(self) -> Iterator[Fsm]:
        return (fsm for fsm in self._fsms if fsm.enable)

    def __getitem__(self, idx: int) -> Fsm:
        return self._fsms[idx]

    def __iter__(self) -> Iterator[Fsm]:
        return iter(self._fsms)

    def __len__(self) -> int:
        return len(self._fsms)
