__all__ = ['parse_bool', 'parse_enum_by_value', 'normalize_keys', 'normalize_enum_str']

from enum import Enum
from typing import Any, Type, Optional, TypeVar, Union

E = TypeVar('E', bound=Enum)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes')
    raise ValueError(f"[parse_bool]  Cannot convert {value!r} to bool")

def parse_enum_by_value(
        value: str | None | Enum,
        enum_cls: Type[Enum],
        allowed_values: Optional[list[str]] = None
) -> Optional[E]:
    """
        Универсальный парсер: принимает строку/None/Enum и возвращает элемент Enum,
        если он есть в allowed_values (список строк — например, имена профилей в конфиге).
    """
    if value in (None, ''):
        return None

    candidate = value.value.lower() if isinstance(value, enum_cls) else str(value).lower()
    if allowed_values is None:
        return enum_cls(candidate)

    allowed_set = {v.lower() for v in allowed_values}
    if candidate in allowed_set:
        return enum_cls(candidate)

    raise ValueError(f"[ConfigWithProfileParser] '{candidate}' not found in allowed values: {allowed_set}")

def normalize_keys(config: dict[str, Any]) -> dict[str, Any]:
    """ Преобразует все ключи словаря к верхнему регистру. Не затрагивает вложенные словари. """
    return {k.upper(): v for k, v in config.items()}

def normalize_enum_str(value: Union[str, Enum], case: str = "lower") -> str:
    """ Преобразует Enum/str в строку, регистр игнорируем """
    if isinstance(value, Enum):
        base = value.value if isinstance(value.value, str) else value.name
    else:
        base = str(value)
    return base.lower() if case.lower() in ("lower", "l") else base.upper()
