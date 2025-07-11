__all__ = ['FieldConverter']

from typing import Any, Callable, Union, Type, get_origin, get_args
from enum import Enum


class FieldConverter:
    """
        Универсальный конвертер значений для парсинга конфигураций.
        Поддерживает:
        - Приведение базовых типов: bool, int, float, str
        - Приведение к Enum
        - Обёртку в list/tuple с приведением элементов
        - Преобразование вложенных структур (tuple of tuples, mapped dict)
        - Преобразование dict → dataclass (через словарь типов)
        - Поддержку Union / Optional
    """

    _custom_converters: dict[type, Callable[[Any], Any]] = {}

    @classmethod
    def register(cls, target_type: type, converter: Callable[[Any], Any]) -> None:
        """ Регистрирует пользовательский конвертер для заданного типа """
        cls._custom_converters[target_type] = converter

    @classmethod
    def convert(cls, value: Any, expected_type: Any) -> Any:
        origin = get_origin(expected_type)
        args = get_args(expected_type)

        # tuple[Type, ...] или list[Type]
        if origin in (tuple, list) and len(args) == 1:
            item_type = args[0]
            if origin is tuple:
                return cls.to_mapped_tuple(value, lambda x: cls.convert(x, item_type))
            return cls.to_list(value, lambda x: cls.convert(x, item_type))

        # Простая проверка на совпадение типов
        if isinstance(expected_type, tuple):
            for t in expected_type:
                if isinstance(value, t):
                    return value
        elif type(expected_type) is type and isinstance(value, expected_type):
            return value

        # Примитивы
        if expected_type is bool:
            return cls.to_bool(value)
        if expected_type is int:
            return cls.to_int(value)
        if expected_type is float:
            return cls.to_float(value)
        if expected_type is str:
            return cls.to_str(value)

        # Enum
        if isinstance(expected_type, type) and issubclass(expected_type, Enum):
            return cls.to_enum(value, expected_type)

        # 💡 Кастомные типы
        if expected_type in cls._custom_converters:
            return cls._custom_converters[expected_type](value)

        raise TypeError(f"Unsupported conversion: {value!r} to {expected_type}")

    @staticmethod
    def to_bool(value: Union[str, int, float, bool, None]) -> bool:
        """ Преобразует значение к булеву типу. """
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "on"}
        raise TypeError(f"Cannot convert {value!r} to bool")

    @staticmethod
    def to_int(value: Union[str, float, bool, int]) -> int:
        """ Преобразует значение к int. """
        try:
            return int(value)
        except (ValueError, TypeError):
            raise TypeError(f"Cannot convert {value!r} to int")

    @staticmethod
    def to_float(value: Union[str, int, bool, float]) -> float:
        """ Преобразует значение к float. """
        try:
            return float(value)
        except (ValueError, TypeError):
            raise TypeError(f"Cannot convert {value!r} to float")

    @staticmethod
    def to_str(value: Union[str, int, float, bool]) -> str:
        """ Преобразует значение к строке. """
        return str(value)

    @staticmethod
    def to_enum(value: Union[str, int, Enum], enum_cls: Type[Enum]) -> Enum:
        """ Преобразует строку или значение к Enum. """
        if isinstance(value, enum_cls):
            return value
        try:
            return enum_cls(value)
        except ValueError:
            try:
                return enum_cls[value.upper()]
            except (KeyError, AttributeError, TypeError):
                raise ValueError(f"Cannot convert {value!r} to enum {enum_cls.__name__}")

    @staticmethod
    def to_tuple(value: Any, item_type: Type) -> tuple:
        """ Преобразует значение в tuple, приводя каждый элемент. """
        if value is None:
            return ()
        if not isinstance(value, (list, tuple)):
            value = [value]
        return tuple(item_type(v) for v in value)

    @staticmethod
    def to_list(value: Any, item_type: Type) -> list:
        """ Преобразует значение в list, приводя каждый элемент. """
        if value is None:
            return []
        if not isinstance(value, (list, tuple)):
            value = [value]
        return [item_type(v) for v in value]

    @staticmethod
    def to_tuple_of_tuples(value: Any, item_mapper: Callable[[Any], Any]) -> tuple[tuple[Any, ...], ...]:
        """ Преобразует список списков в tuple[tuple[...]], с применением item_mapper к каждому элементу. """
        if not isinstance(value, (list, tuple)):
            raise TypeError("Expected sequence of sequences")
        return tuple(
            tuple(item_mapper(v) for v in inner)
            for inner in value
            if isinstance(inner, (list, tuple))
        )

    @staticmethod
    def to_mapped_tuple(value: Union[list[Any], tuple[Any]], item_mapper: Callable[[Any], Any]) -> tuple:
        """ Применяет item_mapper к каждому элементу и возвращает tuple. """
        if not isinstance(value, (list, tuple)):
            raise TypeError("Expected list or tuple")
        return tuple(item_mapper(v) for v in value)

    @staticmethod
    def to_mapped_dict(value: dict[Any, Any], value_mapper: Callable[[Any], Any]) -> dict:
        """ Применяет value_mapper ко всем значениям в словаре. """
        if not isinstance(value, dict):
            raise TypeError("Expected dict")
        return {k: value_mapper(v) for k, v in value.items()}

    @staticmethod
    def to_dict_from_sequence(value: Union[list[dict], tuple[dict]], key_field: str) -> dict:
        """ Преобразует список словарей в словарь по ключу `key_field`. """
        if not isinstance(value, (list, tuple)):
            raise TypeError("Expected sequence of dicts")
        result = {}
        for item in value:
            if not isinstance(item, dict):
                raise TypeError("Each item must be a dict")
            key = item.get(key_field)
            if key is None:
                raise ValueError(f"Missing key_field '{key_field}' in item {item}")
            result[key] = item
        return result

    @staticmethod
    def to_dataclass(value: dict[str, Any], field_types: dict[str, Callable[[Any], Any]], defaults: dict[str, Any] = {}) -> dict[str, Any]:
        """ Приводит словарь значений к полям dataclass с учётом типов и значений по умолчанию. """
        if not isinstance(value, dict):
            raise TypeError("Expected dict")
        result = {}
        for field, caster in field_types.items():
            raw = value.get(field, defaults.get(field))
            if raw is None and field not in defaults:
                raise ValueError(f"Missing required field '{field}'")
            result[field] = caster(raw)
        return result
