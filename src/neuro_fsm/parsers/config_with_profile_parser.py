from __future__ import annotations

__all__ = ['ConfigWithProfileParser']

from typing import Optional, ClassVar

from ..configs import FsmConfig, ProfileConfig
from ..core.profiles import ProfileSwitcherStrategies
from .base_config_parser import BaseconfigParser
from .state_parser import StateConfigParser
from .config_keys import ConfigKeys


class ConfigWithProfileParser(BaseconfigParser):
    """
        Парсер конфигурации машины состояний для формата с профилями.
        Пример входной структуры:
        {
            "ENABLE": true,
            "PROFILE_SWITCHER_STRATEGY": "mixed",
            "STATES": {...},
            "STATE_PROFILES": [
                {
                    "PROFILE_NAME": "default",
                    "STATES": [...],  # optional overrides
                    "EXPECTED_SEQUENCES": [[0, 1, 2]],
                    "INIT_STATES": [0],
                    "DEFAULT_STATES": [0],
                },
            ]
        }
    """

    FIELD_TYPES: ClassVar[dict[str, type | tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, str, int, type(None)),
        ConfigKeys.PROFILE_SWITCHER_STRATEGY: (str, type(None), ProfileSwitcherStrategies),
        ConfigKeys.STATES: (dict, list, tuple),
        ConfigKeys.STATE_PROFILES: (list, tuple),
    }

    def parse(self) -> Optional[FsmConfig]:
        enable = self._parse_bool(self._config.get(ConfigKeys.ENABLE))
        switcher_strategy = self._parse_switcher_strategy(self._config[ConfigKeys.PROFILE_SWITCHER_STRATEGY])
        base_states = StateConfigParser.build_dict(self._config[ConfigKeys.STATES])

        profile_configs: list[ProfileConfig] = []

        for profile in self._config[ConfigKeys.STATE_PROFILES]:
            profile = self._normalize_keys(profile)
            name = self._parse_profile_name(profile[ConfigKeys.PROFILE_NAME])

            profile_states = StateConfigParser.build_dict_with_overrides(
                profile.get(ConfigKeys.STATES, []),
                base_states
            )

            expected_sequences = self._map_sequence(profile[ConfigKeys.EXPECTED_SEQUENCES], profile_states)
            init_states = self._map_state_list(profile[ConfigKeys.INIT_STATES], profile_states)
            default_states = self._map_state_list(profile[ConfigKeys.DEFAULT_STATES], profile_states)

            profile_configs.append(ProfileConfig(
                name=name,
                states=profile_states,
                init_states=init_states,
                default_states=default_states,
                expected_sequences=expected_sequences,
            ))

        if not profile_configs:
            raise ValueError("No valid STATE_PROFILES parsed — check structure and keys")

        return FsmConfig(
            enable=enable,
            switcher_strategy=switcher_strategy,
            states=base_states,
            profiles=tuple(profile_configs),
            meta=self._extract_meta(),
        )
