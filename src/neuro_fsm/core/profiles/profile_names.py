__all__ = ['ProfileNames']

from enum import Enum
from typing import Union, TypeAlias


class ProfileNames(str, Enum):
    SINGLE = "single"
    EMPTY_THEN_FILL = "empty_then_fill"
    FULL_FIRST = "full_first"

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._value2member_map_

# ProfileNameType: TypeAlias = Union[ProfileNames, str]
