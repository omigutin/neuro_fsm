from __future__ import annotations

__all__ = ['SimpleDictParser']

from typing import Optional, ClassVar

from .base_dict_parser import BaseDictParser
from ..state_machine_config import StateMachineConfig
from ..state_profiles import StatesProfileConfig, StateProfileName
from ..config_keys import ConfigKeys


class SimpleDictParser(BaseDictParser):
    """
        Парсер конфигурации машины состояний для простого формата:
        - Поддерживает поля: STATES, EXPECTED_SEQUENCES, INIT_STATES, DEFAULT_STATES
        - Возвращает конфигурацию с одним профилем (DEFAULT)
    """

    FIELD_TYPES: ClassVar[dict[str, type | tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, str, int, type(None)),
        ConfigKeys.STATES: (dict, list, tuple),
        ConfigKeys.EXPECTED_SEQUENCES: (list, tuple),
        ConfigKeys.INIT_STATES: (list, tuple, str, int),
        ConfigKeys.DEFAULT_STATES: (list, tuple, str, int),
    }

    def parse(self) -> Optional[StateMachineConfig]:
        # Преобразование STATES -> tuple[StateMeta, ...]
        self._parse_states(self._config[ConfigKeys.STATES])

        expected_sequences = self._parse_sequences(self._config[ConfigKeys.EXPECTED_SEQUENCES])
        init_states = self._parse_state_tuple(self._config[ConfigKeys.INIT_STATES])
        default_states = self._parse_state_tuple(self._config[ConfigKeys.DEFAULT_STATES])

        profile = StatesProfileConfig(
            name=StateProfileName.DEFAULT,
            states=self._state_configs,
            init_states=init_states,
            default_states=default_states,
            expected_sequences=expected_sequences,
        )

        return StateMachineConfig(
            enable=True,
            switcher_strategy=None,
            states=self._states,
            profiles=(profile,),
            meta=self._extract_meta(),
        )
