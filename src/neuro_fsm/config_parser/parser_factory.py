__all__ = ['ParserFactory']

from types import ModuleType
from typing import Any

from ..configs import FsmConfig
from .config_with_profile_parser import ConfigWithProfileParser
from .simple_config_parser import SimpleConfigParser


class ParserFactory:
    """
        Фабрика парсеров конфигураций машины состояний.
        Определяет тип входного объекта и делегирует соответствующему парсеру.
        Поддерживает: dict, class (type), module (types.ModuleType)
    """

    @classmethod
    def parse(cls, raw_config: Any) -> FsmConfig:
        config: dict[str, Any] = cls._extract_config_dict(raw_config)

        if 'STATE_PROFILES' in config:
            return ConfigWithProfileParser(config).parse()

        if 'STATES' in config and 'EXPECTED_SEQUENCES' in config:
            return SimpleConfigParser(config).parse()

        raise ValueError(f"Unsupported dict structure for state machine config: keys={list(config.keys())}")

    @classmethod
    def _extract_config_dict(cls, raw_config: Any) -> dict[str, Any]:
        """ Создаёт словарь из полученного класса """
        if isinstance(raw_config, dict):
            config = raw_config
        elif isinstance(raw_config, type) or isinstance(raw_config, ModuleType):
            config = {
                k: getattr(raw_config, k) for k in dir(raw_config)
                if not k.startswith('_') and not callable(getattr(raw_config, k))
            }
        elif hasattr(raw_config, '__dict__'):
            config = vars(raw_config)
        else:
            raise TypeError(f"Unsupported config type: {type(raw_config)}")
        return cls._normalize_keys(config)

    @staticmethod
    def _normalize_keys(config: dict[str, Any]) -> dict[str, Any]:
        """ Преобразует все ключи словаря к верхнему регистру. Не затрагивает вложенные словари. """
        return {k.upper(): v for k, v in config.items()}
