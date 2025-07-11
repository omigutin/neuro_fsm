from __future__ import annotations

__all__ = ['BaseDictParser']

from abc import ABC
from typing import Any, Sequence, Optional, ClassVar

from ...models import StatesTuple, StatesTupleTuple, StateParams, StateMeta
from ..config_keys import ConfigKeys
from .base_parser import BaseConfigParser
from .field_converter import FieldConverter


class BaseDictParser(BaseConfigParser, ABC):
    """
        Базовый парсер словарей конфигурации. Отвечает за:
        - Валидацию обязательных полей и типов
        - Преобразование полей с помощью FieldTransformer
        - Преобразование config-класса/модуля/объекта в словарь
        - Парсинг STATES в объекты StateMeta и StateParams
        - Парсинг expected_sequences, init_state, default_state
    """

    FIELD_TYPES: ClassVar[dict[str, type]] = {}

    def __init__(self, config: dict[str, Any]):
        self._config: dict[str, Any] = config
        self._enable: bool = False
        self._states: StatesTuple = ()
        self._state_configs: dict[int, StateParams] = {}

        self._validate()
        self._transform_fields()

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

    def _transform_fields(self) -> None:
        # convertor = FieldConverter()
        for key, expected_type in self.FIELD_TYPES.items():
            if key in self._config:
                self._config[key] = FieldConverter.convert(self._config[key], expected_type)

    def _get_state_by_key(self, key: Any, validate_in_states: bool = True) -> Optional[StateMeta]:
        if isinstance(key, StateMeta):
            return key

        if isinstance(key, dict):
            return StateMeta(cls_id=key['cls_id'], name=str(key['name']), full_name=str(key.get('full_name', "")))

        enum_name = getattr(key, "name", None)
        enum_value = getattr(key, "value", None)
        full_name = getattr(key, "full_name", None)
        if isinstance(enum_name, str) and isinstance(enum_value, int):
            return StateMeta(cls_id=enum_value, name=enum_name, full_name=full_name or enum_name)

        if validate_in_states:
            return self._validate_in_states(key)

        return None

    def _validate_in_states(self, key: Any) -> Optional[StateMeta]:
        if not self._states:
            raise RuntimeError("Call _parse_states() first")
        name_map = {s.name: s for s in self._states}
        id_map = {s.cls_id: s for s in self._states}
        if isinstance(key, int):
            return id_map.get(key) or self.__raise_not_found(key)
        if isinstance(key, str):
            return name_map.get(key) or self.__raise_not_found(key)
        self.__raise_not_found(key)

    def __raise_not_found(self, key: Any) -> None:
        raise ValueError(f"StateMeta '{key}' not found in base states")

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
