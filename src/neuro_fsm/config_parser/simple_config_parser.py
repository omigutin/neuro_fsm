__all__ = ['SimpleConfigParser']

from typing import Optional, ClassVar
from ..configs import FsmConfig, ProfileConfig
from .base_config_parser import BaseconfigParser
from .state_config_parser import StateConfigParser
from .config_keys import ConfigKeys
from ..core.profiles import ProfileNames

class SimpleConfigParser(BaseconfigParser):
    """
        Парсер простой конфигурации машины состояний без поддержки профилей.
    """

    FIELD_TYPES: ClassVar[dict[str, type | tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, int, str, type(None)),
        ConfigKeys.STATES: (list, tuple, dict),
        ConfigKeys.EXPECTED_SEQUENCES: (list, tuple),
        ConfigKeys.INIT_STATES: (int, str),
        ConfigKeys.DEFAULT_STATES: (int, str),
    }

    def parse(self) -> Optional[FsmConfig]:
        enable = self._parse_bool(self._config.get(ConfigKeys.ENABLE))

        base_states = StateConfigParser.build_dict(self._config[ConfigKeys.STATES])
        expected_sequences = self._map_sequence(self._config[ConfigKeys.EXPECTED_SEQUENCES], base_states)
        init_states = self._map_state_list([self._config[ConfigKeys.INIT_STATES]], base_states)
        default_states = self._map_state_list([self._config[ConfigKeys.DEFAULT_STATES]], base_states)

        profile = ProfileConfig(
            name=ProfileNames.SINGLE,
            states=base_states,
            expected_sequences=expected_sequences,
            init_states=init_states,
            default_states=default_states,
        )

        return FsmConfig(
            enable=enable,
            switcher_strategy=None,
            states=base_states,
            profiles=(profile,),
            meta=self._extract_meta(),
        )
