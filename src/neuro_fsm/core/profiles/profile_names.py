__all__ = ['ProfileNames']

from enum import Enum


class ProfileNames(str, Enum):
    DEFAULT = "default"
    EMPTY_THEN_FILL = "empty_then_fill"
    FULL_FIRST = "full_first"

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._value2member_map_
