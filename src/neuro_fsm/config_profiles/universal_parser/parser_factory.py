__all__ = ['ParserFactory']

from types import ModuleType
from typing import Any

from ..state_machine_config import StateMachineConfig
from ..config_keys import ConfigKeys
from .simple_dict_parser import SimpleDictParser
from .profile_dict_parser import ProfileDictParser


class ParserFactory:
    """
        Фабрика парсеров конфигураций машины состояний.
        Определяет тип входного объекта и делегирует соответствующему парсеру.
        Поддерживает: dict, class (type), module (types.ModuleType)
    """

    @classmethod
    def parse(cls, raw_config: Any) -> StateMachineConfig:
        config: dict[str, Any] = cls._extract_config_dict(raw_config)

        if ConfigKeys.STATE_PROFILES in config:
            return ProfileDictParser(config).parse()

        if ConfigKeys.STATES in config and ConfigKeys.EXPECTED_SEQUENCES in config:
            return SimpleDictParser(config).parse()

        raise ValueError("Unsupported dict structure for state machine config")

    @classmethod
    def _extract_config_dict(cls, raw_config: Any) -> dict[str, Any]:
        """ Создаёт словарь из полученного класса """
        if isinstance(raw_config, dict):
            config = raw_config
        elif isinstance(raw_config, type) or isinstance(raw_config, ModuleType):
            config = {k: getattr(raw_config, k) for k in dir(raw_config) if not k.startswith('_') and not callable(getattr(raw_config, k))}
        elif hasattr(raw_config, '__dict__'):
            config = vars(raw_config)
        else:
            raise TypeError(f"Unsupported config type: {type(raw_config)}")
        return cls._normalize_keys(config)

    @staticmethod
    def _normalize_keys(config: dict[str, Any]) -> dict[str, Any]:
        """ Преобразует все ключи словаря к верхнему регистру. Не затрагивает вложенные словари. """
        return {k.upper(): v for k, v in config.items()}
