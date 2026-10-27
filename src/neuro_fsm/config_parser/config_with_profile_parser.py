from __future__ import annotations

__all__ = ['ConfigWithProfileParser']

from enum import Enum
from typing import Any, ClassVar, Mapping, Optional

from ..configs import FsmConfig, ProfileConfig
from ..configs.state_config import StateConfigDict
from ..models import ProfileNames
from ..utils.type_normalizer import TypeNormalizer
from .base_config_parser import BaseConfigParser
from .config_keys import ConfigKeys
from .state_config_parser import StateConfigParser


class ConfigWithProfileParser(BaseConfigParser):
    """
        Конфигурация с профилями:
        {
            "ENABLE": True,
            "STATES": [...],                                  # базовые состояния всех профилей
            "STATE_PROFILES": [
                {
                    "NAME": "group1",
                    "STATES": {"EMPTY": {"stable_min_lim": 5}},  # переопределения: имя/cls_id/Enum → поля
                    "EXPECTED_SEQUENCES": [["EMPTY", "FULL", "EMPTY"]],
                    "INIT_STATES": ["EMPTY"],
                    "DEFAULT_STATES": ["UNKNOWN"],
                },
            ],
            "PROFILE_SWITCHER_STRATEGY": "BY_MAPPED_ID",
            "DEFAULT_PROFILE": "default",
            "PROFILE_IDS_MAP": {"group1": [101, 102], "default": []},
            "RAW_HISTORY_WRITER": {...}, "STABLE_HISTORY_WRITER": {...},
        }
        Если DEFAULT_PROFILE не задан: единственный профиль, иначе профиль 'default', иначе единственный
        профиль с пустым списком id в PROFILE_IDS_MAP.
    """

    REQUIRED_FIELDS: ClassVar[tuple[str, ...]] = (ConfigKeys.STATES, ConfigKeys.STATE_PROFILES)
    FIELD_TYPES: ClassVar[dict[str, tuple[type, ...]]] = {
        ConfigKeys.ENABLE: (bool, str, int, type(None)),
        ConfigKeys.STATES: (dict, list, tuple),
        ConfigKeys.STATE_PROFILES: (list, tuple),
        ConfigKeys.PROFILE_SWITCHER_STRATEGY: (str, Enum, type(None)),
        ConfigKeys.DEFAULT_PROFILE: (str, Enum, type(None)),
        ConfigKeys.PROFILE_IDS_MAP: (dict, type(None)),
        ConfigKeys.RAW_HISTORY_WRITER: (dict, type(None)),
        ConfigKeys.STABLE_HISTORY_WRITER: (dict, type(None)),
    }

    def parse(self) -> FsmConfig:
        builder = self._create_builder()
        base_states = StateConfigParser.build_dict(self._config[ConfigKeys.STATES])

        for raw_profile in self._config[ConfigKeys.STATE_PROFILES]:
            builder.add_profile(self._parse_profile(raw_profile, base_states))
        if not builder.list_profiles():
            raise ValueError(f"'{ConfigKeys.STATE_PROFILES}' is empty")

        ids_map: Mapping[Any, Any] = self._config.get(ConfigKeys.PROFILE_IDS_MAP) or {}
        builder.set_profile_ids_map(ids_map)
        builder.set_default_profile(self._choose_default_profile(builder.list_profiles(), ids_map))
        return builder.build()

    def _parse_profile(self, raw_profile: Any, base_states: StateConfigDict) -> ProfileConfig:
        """ Профиль: копия базовых состояний + переопределения + init/default/sequences. """
        if not isinstance(raw_profile, Mapping):
            raise TypeError(f"Each item of '{ConfigKeys.STATE_PROFILES}' must be a dict, got {type(raw_profile)!r}")
        data = TypeNormalizer.normalize_dict_keys(dict(raw_profile), case="upper")
        unknown = set(data) - ConfigKeys.PROFILE_KEYS
        if unknown:
            raise ValueError(f"Profile has unknown keys: {sorted(unknown)}")

        profile = ProfileConfig(
            name=self._profile_name(data.get(ConfigKeys.PROFILE_NAME)),
            states=dict(base_states),
            description=str(data.get(ConfigKeys.PROFILE_DESCRIPTION, "")),
        )
        overrides = data.get(ConfigKeys.STATES) or {}
        if not isinstance(overrides, Mapping):
            raise TypeError(f"Profile '{profile.name}': '{ConfigKeys.STATES}' must be a dict of overrides")
        for ref, patch in overrides.items():
            if not isinstance(patch, Mapping):
                raise TypeError(f"Profile '{profile.name}': override for {ref!r} must be a dict")
            state = self._resolve_state(profile, ref, ConfigKeys.STATES)
            try:
                profile.update_state(state, **patch)
            except TypeError as exc:
                raise ValueError(f"Profile '{profile.name}': invalid override for {ref!r}: {exc}") from exc

        profile.set_init_states(self._resolve_states(
            profile, self._get_states_field(data, ConfigKeys.INIT_STATES, ConfigKeys.INIT_STATE),
            ConfigKeys.INIT_STATES,
        ))
        profile.set_default_states(self._resolve_states(
            profile, self._get_states_field(data, ConfigKeys.DEFAULT_STATES, ConfigKeys.DEFAULT_STATE),
            ConfigKeys.DEFAULT_STATES,
        ))
        profile.set_expected_sequences(self._resolve_sequences(profile, data.get(ConfigKeys.EXPECTED_SEQUENCES)))
        return profile

    def _choose_default_profile(self, names: tuple[str, ...], ids_map: Mapping[Any, Any]) -> str:
        """ Имя профиля по умолчанию (см. описание класса). """
        raw: Optional[Any] = self._config.get(ConfigKeys.DEFAULT_PROFILE)
        if raw is not None:
            return TypeNormalizer.normalize_to_str_name(raw, case="lower")
        if len(names) == 1:
            return names[0]
        if ProfileNames.DEFAULT.value in names:
            return ProfileNames.DEFAULT.value
        empty = [TypeNormalizer.normalize_to_str_name(k, case="lower") for k, ids in ids_map.items() if not ids]
        if len(empty) == 1:
            return empty[0]
        raise ValueError(f"'{ConfigKeys.DEFAULT_PROFILE}' is not set and cannot be determined")
