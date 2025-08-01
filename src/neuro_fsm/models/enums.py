__all__ = ['ProfileSwitcherStrategies', 'ProfileNames']

from enum import Enum, auto


class ProfileSwitcherStrategies(Enum):
    """ Стратегии переключения профиля. """

    MANUAL = auto()            # Ручная смена профиля
    BY_MATCH = auto()          # Если какой-либо профиль завершил последовательность
    BY_EXCLUSION = auto()      # Если все профили, кроме одного, точно невалидны
    MIXED = auto()             # Сначала match, иначе если остался один возможный — активируем


class ProfileNames(str, Enum):
    DEFAULT = "default"
    SINGLE = "single"
    EMPTY_THEN_FILL = "empty_then_fill"
    FULL_FIRST = "full_first"

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._value2member_map_
