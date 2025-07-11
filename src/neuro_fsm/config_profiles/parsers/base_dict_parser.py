__all__ = ['BaseDictParser']

from abc import ABC
from typing import Any, ClassVar

from ...models import StatesDict, State, StatesTupleTuple, StatesTuple
from ..state_profiles import StateProfileName, ProfileSwitcherStrategy
from ..config_keys import ConfigKeys


class BaseDictParser(ABC):

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
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    def _validate_field_types(self) -> None:
        for key, expected_types in self.FIELD_TYPES.items():
            if key in self._config and not isinstance(self._config[key], expected_types):
                raise TypeError(f"Field '{key}' must be of type {expected_types}")

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ('1', 'true', 'yes')
        raise ValueError(f"[ProfileDictParser] Cannot convert {value!r} to bool")

    @staticmethod
    def _parse_profile_name(value: str) -> StateProfileName:
        return StateProfileName(value)

    @staticmethod
    def _parse_switcher_strategy(value: str) -> ProfileSwitcherStrategy:
        return ProfileSwitcherStrategy(value)

    @staticmethod
    def _map_sequence(seq_list: list[list[State]], state_dict: StatesDict) -> StatesTupleTuple:
        return tuple(
            tuple(state_dict[s.cls_id] for s in seq if s.cls_id in state_dict)
            for seq in seq_list
        )

    @staticmethod
    def _map_state_list(state_list: list[State], state_dict: StatesDict) -> StatesTuple:
        return tuple(state_dict[s.cls_id] for s in state_list if s.cls_id in state_dict)

    def _extract_meta(self) -> dict[str, Any]:
        return {
            k.lower(): v
            for k, v in self._config.items()
            if k not in ConfigKeys.ALL
        }

    @staticmethod
    def _normalize_keys(config: dict[str, Any]) -> dict[str, Any]:
        """ Преобразует все ключи словаря к верхнему регистру. Не затрагивает вложенные словари. """
        return {k.upper(): v for k, v in config.items()}
