__all__ = ['parse_bool', 'normalize_keys', 'normalize_enum_str']

from enum import Enum
from typing import Any, Type, Optional, TypeVar, Union

E = TypeVar('E', bound=Enum)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes')
    raise ValueError(f"[parse_bool]  Cannot convert {value!r} to bool")

def normalize_keys(config: dict[str, Any]) -> dict[str, Any]:
    """ Преобразует все ключи словаря к верхнему регистру. Не затрагивает вложенные словари. """
    return {k.upper(): v for k, v in config.items()}

def normalize_enum_str(value: Union[str, Enum], case: str = "lower") -> str:
    """ Приводит Enum/str к строке-ключу в нужном регистре. """
    if isinstance(value, Enum):
        base = value.value if isinstance(value.value, str) else value.name
    else:
        base = str(value)
    return base.lower() if case.lower() in ("lower", "l") else base.upper()
