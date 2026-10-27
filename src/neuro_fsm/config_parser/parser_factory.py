__all__ = ['ParserFactory']

from types import ModuleType
from typing import Any, Mapping

from ..configs import FsmConfig
from ..utils.type_normalizer import TypeNormalizer
from .config_keys import ConfigKeys
from .parsing_utils import parse_bool


class ParserFactory:
    """
        Разбор конфигурации из dict, класса или модуля.
        Формат определяется по ключам: STATE_PROFILES — с профилями, иначе STATES — простой.
        Если ENABLE ложно, остальные поля не разбираются и возвращается выключенная конфигурация.
    """

    @classmethod
    def parse(cls, raw_config: Any) -> FsmConfig:
        from .config_with_profile_parser import ConfigWithProfileParser
        from .simple_config_parser import SimpleConfigParser

        config = cls.extract_config_to_dict(raw_config)

        if not parse_bool(config.get(ConfigKeys.ENABLE), default=True):
            meta = {k.lower(): v for k, v in config.items() if k not in ConfigKeys.ALL}
            return FsmConfig.create_disabled(meta=meta)
        if ConfigKeys.STATE_PROFILES in config:
            return ConfigWithProfileParser(config).parse()
        if ConfigKeys.STATES in config:
            return SimpleConfigParser(config).parse()
        raise ValueError(f"Unsupported state machine config structure: keys={sorted(config.keys())}")

    @staticmethod
    def extract_config_to_dict(raw_config: Any) -> dict[str, Any]:
        """ Публичные некаллабельные атрибуты класса/модуля или dict → dict с ключами в верхнем регистре. """
        if isinstance(raw_config, Mapping):
            config = dict(raw_config)
        elif isinstance(raw_config, (type, ModuleType)):
            config = {
                k: getattr(raw_config, k) for k in dir(raw_config)
                if not k.startswith('_') and not callable(getattr(raw_config, k))
            }
        elif hasattr(raw_config, '__dict__'):
            config = {k: v for k, v in vars(raw_config).items() if not k.startswith('_')}
        else:
            raise TypeError(f"Unsupported config type: {type(raw_config)!r}")
        return TypeNormalizer.normalize_dict_keys(config, case="upper")
