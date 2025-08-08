__all__ = ['BaseconfigParser']

from abc import ABC
from enum import Enum
from typing import Any, ClassVar, Union, Iterable

from ..configs import StateConfig, StateConfigDict, StateConfigTuple, StateConfigTupleTuple, ProfileConfig
from ..configs.history_writer_config import HistoryWriterConfig
from ..models import ProfileSwitcherStrategies, ProfileNames
from .parsing_utils import normalize_enum_str
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
    def _parse_profile_name(name: ProfileNames | str) -> str:
        try:
            return ProfileNames[name.upper()].value
        except KeyError:
            return name

    @staticmethod
    def _parse_switcher_strategy(value: str | None | ProfileSwitcherStrategies) -> ProfileSwitcherStrategies:
        if value is None:
            return ProfileSwitcherStrategies.SINGLE
        if isinstance(value, Enum):
            return ProfileSwitcherStrategies[value.name]
        if isinstance(value, str):
            try:
                return ProfileSwitcherStrategies[value.upper()]
            except KeyError:
                raise ValueError(f"ProfileSwitcherStrategies has no member '{value}'")
        raise TypeError(f"Cannot parse ProfileSwitcherStrategies from value: {value!r}")

    @staticmethod
    def _parse_profile_ids_map(value: Union[dict[str, Any], None]) -> dict[str, list[Any]]:
        """
            Приводит словарь {profile_name: [id1, id2, ...]} к виду с строковыми ключами и списками значений.
            Пустой список означает профиль по умолчанию.
        """
        if value is None:
            return {}
        result = {}
        for raw_key, raw_ids in value.items():
            key = normalize_enum_str(raw_key, case="lower")
            if raw_ids is None:
                result[key] = []
            elif isinstance(raw_ids, Iterable) and not isinstance(raw_ids, (str, bytes)):
                result[key] = list(raw_ids)
            else:
                raise ValueError(f"Profile '{key}' must be assigned to a list/tuple of IDs or None, got: {type(raw_ids)}")
        return result

    @staticmethod
    def _parse_default_profile(name: str | None | ProfileNames, profile_configs: list['ProfileConfig']) -> ProfileNames:
        """
            Возвращает название профиля по логике выбора default_profile.
            Если профиля нет — бросает ValueError.
            Если профайлов не задано — возвращает ProfileNames.SINGLE.
        """
        if not profile_configs or name is None:
            return ProfileNames.SINGLE
        # Получаем список допустимых имён профилей (ProfileNames или str)
        valid_names = {str(p.name).upper(): p.name for p in profile_configs}
        if isinstance(name, Enum):
            def_profile = name
        elif isinstance(name, str):
            key = name.upper()
            if key in valid_names:
                def_profile = valid_names[key]
            else:
                raise ValueError(f"ProfileNames has no member '{name}'")
        else:
            raise TypeError(f"Cannot parse ProfileNames from value: {name!r}")
        # Проверяем, что профиль есть среди распарсенных профилей
        if def_profile not in [p.name for p in profile_configs]:
            raise ValueError(
                f"Profile '{def_profile}' not found in parsed profiles: {[p.name for p in profile_configs]}")
        return def_profile

    @staticmethod
    def _parse_history_writer_config(data: dict[str, Any] | None) -> HistoryWriterConfig:
        if data is None:
            return HistoryWriterConfig(
                name="",
                fields=(),
                enable=False,
                max_age_days=14,
                async_mode=False
            )
        # Поля обязательно tuple
        fields = data.get("fields", ())
        if isinstance(fields, list):
            fields = tuple(fields)
        # Конструктор
        return HistoryWriterConfig(
            name=data["name"],
            fields=fields,
            enable=data.get("enable", False),
            max_age_days=int(data.get("max_age_days", 14)),
            async_mode=bool(data.get("async_mode", False))
        )

    @staticmethod
    def _map_sequence(seq_list: list, state_configs: StateConfigDict) -> StateConfigTupleTuple:
        """
            seq_list: список последовательностей, состояний (строк, int, Enum или StateConfig)
            state_configs: словарь {cls_id: StateConfig}
        """
        # Создаём доп. индекс: name → StateConfig (на всякий случай)
        name2cfg = {cfg.name: cfg for cfg in state_configs.values()}
        id2cfg = state_configs

        def resolve(item):
            if isinstance(item, StateConfig):
                return item
            elif isinstance(item, int) and item in id2cfg:
                return id2cfg[item]
            elif isinstance(item, str) and item in name2cfg:
                return name2cfg[item]
            elif hasattr(item, "name") and item.name in name2cfg:
                # Для Enum
                return name2cfg[item.name]
            else:
                raise ValueError(f"Unknown state reference: {item!r}")

        return tuple(
            tuple(resolve(s) for s in seq)
            for seq in seq_list
        )

    @staticmethod
    def _map_state_list(state_list, state_dict: StateConfigDict) -> StateConfigTuple:
        if not isinstance(state_list, (list, tuple, set)):
            state_list = (state_list,)

        # Индексы для поиска
        name2cfg = {cfg.name: cfg for cfg in state_dict.values()}
        id2cfg = state_dict

        def resolve(item):
            if isinstance(item, StateConfig):
                return item
            elif isinstance(item, int) and item in id2cfg:
                return id2cfg[item]
            elif isinstance(item, str) and item in name2cfg:
                return name2cfg[item]
            elif hasattr(item, "name") and item.name in name2cfg:
                # Для Enum
                return name2cfg[item.name]
            else:
                raise ValueError(f"Unknown state reference: {item!r}")

        return tuple(resolve(s) for s in state_list)

    def _extract_meta(self) -> dict[str, Any]:
        return {
            k.lower(): v
            for k, v in self._config.items()
            if k not in ConfigKeys.ALL
        }
