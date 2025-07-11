from __future__ import annotations

__all__ = ['ProfileDictParser']

from typing import Optional, ClassVar

from .field_converter import FieldConverter
from ...models import StateParams, StatesTuple
from ..state_machine_config import StateMachineConfig
from ..state_profiles import StatesProfileConfig, StateProfileName, ProfileSwitcherStrategy
from ..config_keys import ConfigKeys
from .base_dict_parser import BaseDictParser


class ProfileDictParser(BaseDictParser):
    """
        Парсер конфигурации STATE_PROFILES:
        - Поддерживает словари состояний (dict[имя|id|Enum, параметры])
        - Поддерживает список профилей, каждый со своей конфигурацией
    """

    FIELD_TYPES: ClassVar[dict[str, type | tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, str, int, type(None)),
        ConfigKeys.PROFILE_SWITCHER_STRATEGY: (str, type(None), ProfileSwitcherStrategy),
        ConfigKeys.STATES: (dict, list, tuple),
        ConfigKeys.STATE_PROFILES: (list, tuple),
    }

    def parse(self) -> Optional[StateMachineConfig]:
        from ...models import StatesTupleTuple

        self._enable = FieldConverter.convert(
            self._config[ConfigKeys.ENABLE],
            bool
        )

        self._states = FieldConverter.convert(
            self._config[ConfigKeys.STATES],
            StatesTuple
        )

        profile_switcher = FieldConverter.convert(
            self._config[ConfigKeys.PROFILE_SWITCHER_STRATEGY],
            ProfileSwitcherStrategy
        )

        raw_profiles = self._config.get(ConfigKeys.STATE_PROFILES, ())
        profiles: list[StatesProfileConfig] = []
        for raw_profile in raw_profiles:
            raw_profile = self._normalize_keys(raw_profile)

            profile_name = FieldConverter.convert(
                raw_profile[ConfigKeys.PROFILE_NAME],
                StateProfileName
            )

            expected_sequences = FieldConverter.convert(
                raw_profile[ConfigKeys.EXPECTED_SEQUENCES],
                StatesTupleTuple
            )

            init_states = FieldConverter.convert(
                raw_profile[ConfigKeys.INIT_STATES],
                StatesTuple
            )

            default_states = FieldConverter.convert(
                raw_profile[ConfigKeys.DEFAULT_STATES],
                StatesTuple
            )

            raw_state_configs = raw_profile.get(ConfigKeys.STATES, {})
            state_configs = {
                self._get_state_by_key(k).cls_id: FieldConverter.convert(v, StateParams)
                for k, v in raw_state_configs.items()
            }

            profiles.append(StatesProfileConfig(
                name=profile_name,
                states=state_configs,
                init_states=init_states,
                default_states=default_states,
                expected_sequences=expected_sequences,
            ))

        return StateMachineConfig(
            enable=self._enable,
            switcher_strategy=profile_switcher,
            states=self._states,
            profiles=tuple(profiles),
            meta=self._extract_meta()
        )
