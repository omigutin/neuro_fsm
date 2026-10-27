__all__ = ['SimpleConfigParser']

from typing import ClassVar

from ..configs import FsmConfig, ProfileConfig
from ..models import ProfileNames
from .base_config_parser import BaseConfigParser
from .config_keys import ConfigKeys
from .state_config_parser import StateConfigParser


class SimpleConfigParser(BaseConfigParser):
    """
        Конфигурация без профилей (формат pc_develop):
            ENABLE, STATES, EXPECTED_SEQUENCES, INIT_STATE(S), DEFAULT_STATE(S).
        Создаётся один профиль 'single'.
    """

    REQUIRED_FIELDS: ClassVar[tuple[str, ...]] = (ConfigKeys.STATES,)
    FIELD_TYPES: ClassVar[dict[str, tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, int, str, type(None)),
        ConfigKeys.STATES: (list, tuple, dict),
        ConfigKeys.EXPECTED_SEQUENCES: (list, tuple, type(None)),
    }

    def parse(self) -> FsmConfig:
        builder = self._create_builder()
        profile = ProfileConfig(
            name=ProfileNames.SINGLE,
            states=StateConfigParser.build_dict(self._config[ConfigKeys.STATES]),
        )
        profile.set_init_states(self._resolve_states(
            profile, self._get_states_field(self._config, ConfigKeys.INIT_STATES, ConfigKeys.INIT_STATE),
            ConfigKeys.INIT_STATES,
        ))
        profile.set_default_states(self._resolve_states(
            profile, self._get_states_field(self._config, ConfigKeys.DEFAULT_STATES, ConfigKeys.DEFAULT_STATE),
            ConfigKeys.DEFAULT_STATES,
        ))
        profile.set_expected_sequences(
            self._resolve_sequences(profile, self._config.get(ConfigKeys.EXPECTED_SEQUENCES))
        )
        builder.add_profile(profile, default=True)
        return builder.build()
