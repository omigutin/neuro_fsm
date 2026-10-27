__all__ = ['parse_bool']

from typing import Any


def parse_bool(value: Any, default: bool) -> bool:
    """ Приводит bool / int / str / None к bool. None → default. """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ('1', 'true', 'yes', 'on'):
            return True
        if normalized in ('0', 'false', 'no', 'off', ''):
            return False
    raise ValueError(f"[parse_bool] Cannot convert {value!r} to bool")
