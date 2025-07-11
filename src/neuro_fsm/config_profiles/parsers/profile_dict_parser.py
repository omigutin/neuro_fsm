from __future__ import annotations

__all__ = ['ProfileDictParser']

from typing import Optional, ClassVar

from .base_dict_parser import BaseDictParser
from .state_parser import StateParser
from ..config_keys import ConfigKeys
from ..state_machine_config import StateMachineConfig
from ..state_profiles import StatesProfileConfig, ProfileSwitcherStrategy
from ..state_profiles.states_profile import StatesProfile
from ...models import StatesTuple, StatesTupleTuple


class ProfileDictParser(BaseDictParser):
    """
        Парсер конфигурации машины состояний для формата с профилями.
        Поддерживает поля:
        - ENABLE, PROFILE_SWITCHER_STRATEGY
        - STATES, STATE_PROFILES (с expected_sequences, init_states, default_states)
        - Возвращает StateMachineConfig с заполненными StatesProfileConfig
    """

    FIELD_TYPES: ClassVar[dict[str, type | tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, str, int, type(None)),
        ConfigKeys.PROFILE_SWITCHER_STRATEGY: (str, type(None), ProfileSwitcherStrategy),
        ConfigKeys.STATES: (dict, list, tuple),
        ConfigKeys.STATE_PROFILES: (list, tuple),
    }

    def parse(self) -> Optional[StateMachineConfig]:
        enable = self._parse_bool(self._config.get(ConfigKeys.ENABLE))
        switcher_strategy = self._parse_switcher_strategy(self._config[ConfigKeys.PROFILE_SWITCHER_STRATEGY])
        global_states = StateParser.build_states_dict(self._config[ConfigKeys.STATES])

        profile_configs: list[StatesProfile] = []

        for profile in self._config[ConfigKeys.STATE_PROFILES]:
            self._normalize_keys(profile)

            name = self._parse_profile_name(profile[ConfigKeys.PROFILE_NAME])

            overrides_raw = profile.get(ConfigKeys.STATES, [])
            profile_states = StateParser.override_states(global_states, overrides_raw)

            expected_sequences: StatesTupleTuple = self._map_sequence(profile[ConfigKeys.EXPECTED_SEQUENCES], profile_states)
            init_states: StatesTuple = self._map_state_list(profile[ConfigKeys.INIT_STATES], profile_states)
            default_states: StatesTuple = self._map_state_list(profile[ConfigKeys.DEFAULT_STATES], profile_states)

            profile_configs.append(StatesProfile(StatesProfileConfig(
                name=name,
                states=profile_states,
                init_states=init_states,
                default_states=default_states,
                expected_sequences=expected_sequences,
            )))

        return StateMachineConfig(
            enable=enable,
            switcher_strategy=switcher_strategy,
            states=global_states,
            profiles=tuple(profile_configs),
            meta=self._extract_meta(),
        )
