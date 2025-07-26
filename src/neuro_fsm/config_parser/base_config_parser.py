__all__ = ['BaseconfigParser']

from abc import ABC
from typing import Any, ClassVar

from .parsing_utils import parse_enum_by_value
from ..configs import StateConfig, StateConfigDict, StateConfigTuple, StateConfigTupleTuple, ProfileConfig
from ..core.profiles import ProfileNames, ProfileSwitcherStrategies
from .config_keys import ConfigKeys


class BaseconfigParser(ABC):

    FIELD_TYPES: ClassVar[dict[str, type]] = {}

    def __init__(self, config: dict[str, Any]):
        self._config: dict[str, Any] = config
        self._validate()

    def _validate(self) -> None:
        self._validate_required_fields()
        self._validate_field_types()

    def _validate_required_fields(self) -> None:
        missing = [field for field in self.FIELD_TYPES if field not in self._config]
        if missing:
            raise ValueError(f"[{self.__class__.__name__}] Missing required fields: {', '.join(missing)}")

    def _validate_field_types(self) -> None:
        for key, expected_types in self.FIELD_TYPES.items():
            if key in self._config and not isinstance(self._config[key], expected_types):
                raise TypeError(f"[{self.__class__.__name__}] Field '{key}' must be of type {expected_types}")

    @staticmethod
    def _parse_profile_name(value: str) -> ProfileNames:
        return ProfileNames(value)

    @staticmethod
    def _parse_switcher_strategy(value: str | None | ProfileSwitcherStrategies) -> ProfileSwitcherStrategies:
        strategy = parse_enum_by_value(value, ProfileSwitcherStrategies)
        return strategy if strategy else ProfileSwitcherStrategies.MIXED

    @staticmethod
    def _parse_default_profile(value: str | None | ProfileNames, profile_configs: list[ProfileConfig]) -> ProfileNames:
        """ Возвращает название профиля по логике выбора default_profile. """
        if not profile_configs:
            return ProfileNames.DEFAULT
        def_profile = parse_enum_by_value(value, ProfileNames, [p.name for p in profile_configs])
        return def_profile if def_profile else ProfileNames.DEFAULT

    @staticmethod
    def _map_sequence(seq_list: list[list[StateConfig]], state_dict: StateConfigDict) -> StateConfigTupleTuple:
        return tuple(
            tuple(state_dict[s.cls_id] for s in seq if s.cls_id in state_dict)
            for seq in seq_list
        )

    @staticmethod
    def _map_state_list(state_list: list[StateConfig], state_dict: StateConfigDict) -> StateConfigTuple:
        return tuple(state_dict[s.cls_id] for s in state_list if s.cls_id in state_dict)

    def _extract_meta(self) -> dict[str, Any]:
        return {
            k.lower(): v
            for k, v in self._config.items()
            if k not in ConfigKeys.ALL
        }
