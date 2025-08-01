from __future__ import annotations

__all__ = ['ConfigWithProfileParser']

from enum import Enum
from typing import Optional, ClassVar

from ..configs import FsmConfig, ProfileConfig
from .base_config_parser import BaseconfigParser
from .state_config_parser import StateConfigParser
from .config_keys import ConfigKeys
from .parsing_utils import normalize_keys, parse_bool


class ConfigWithProfileParser(BaseconfigParser):
    """
        Парсер конфигурации машины состояний для формата с профилями.
        Пример входной структуры:
        {
            "ENABLE": true,
            "STATES": {...},
            "STATE_PROFILES": [
                {
                    "PROFILE_NAME": "single",
                    "STATES": [...], # optional overrides
                    "EXPECTED_SEQUENCES": [[0, 1, 2]],
                    "INIT_STATES": [0],
                    "DEFAULT_STATES": [0],
                },
            ],
            "PROFILE_SWITCHER_STRATEGY": "mixed",
            "DEFAULT_PROFILE": ProfileNames.EMPTY_THEN_FILL,
        }
    """

    FIELD_TYPES: ClassVar[dict[str, type | tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, str, int, type(None)),
        ConfigKeys.STATES: (dict, list, tuple),
        ConfigKeys.STATE_PROFILES: (list, tuple),
        ConfigKeys.PROFILE_SWITCHER_STRATEGY: (str, type(None), Enum),
        ConfigKeys.DEFAULT_PROFILE: (str, type(None), Enum),
    }

    def parse(self) -> Optional[FsmConfig]:
        enable = parse_bool(self._config.get(ConfigKeys.ENABLE))
        switcher_strategy = self._parse_switcher_strategy(self._config[ConfigKeys.PROFILE_SWITCHER_STRATEGY])
        base_state_configs = StateConfigParser.build_dict(self._config[ConfigKeys.STATES])

        profile_configs: list[ProfileConfig] = []

        for profile in self._config[ConfigKeys.STATE_PROFILES]:
            profile = normalize_keys(profile)
            name = self._parse_profile_name(profile[ConfigKeys.PROFILE_NAME])

            profile_state_configs = StateConfigParser.build_dict_with_overrides(
                profile.get(ConfigKeys.STATES, {}),
                base_state_configs
            )

            expected_sequences = self._map_sequence(profile[ConfigKeys.EXPECTED_SEQUENCES], profile_state_configs)
            init_states = self._map_state_list(profile[ConfigKeys.INIT_STATES], profile_state_configs)
            default_states = self._map_state_list(profile[ConfigKeys.DEFAULT_STATES], profile_state_configs)

            profile_configs.append(ProfileConfig(
                name=name,
                states=profile_state_configs,
                init_states=init_states,
                default_states=default_states,
                expected_sequences=expected_sequences,
            ))

        if not profile_configs:
            raise ValueError("No valid STATE_PROFILES parsed — check structure and keys")

        def_profile = self._parse_default_profile(self._config[ConfigKeys.DEFAULT_PROFILE], profile_configs)

        return FsmConfig(
            enable=enable,
            state_configs=base_state_configs,
            profiles=tuple(profile_configs),
            switcher_strategy=switcher_strategy,
            def_profile=def_profile,
            meta=self._extract_meta(),
        )
