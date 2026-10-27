from __future__ import annotations

__all__ = ['ProfileSwitcherStrategies', 'ProfileNames']

from enum import Enum, auto
from typing import Union


class ProfileSwitcherStrategies(Enum):
    """ Стратегии автоматического переключения активного профиля. """
    SINGLE = auto()            # Автоматического переключения нет (только вручную по имени)
    BY_MAPPED_ID = auto()      # Профиль выбирается вручную по внешнему id (switch_profile_by_pid)
    BY_MATCH = auto()          # Переключение на профиль, завершивший ожидаемую последовательность
    BY_EXCLUSION = auto()      # Переключение, если совпадение возможно только у одного профиля
    MIXED = auto()             # Сначала BY_MATCH, затем BY_EXCLUSION

    @classmethod
    def parse(cls, value: Union[ProfileSwitcherStrategies, Enum, str, None]) -> ProfileSwitcherStrategies:
        """ Приводит Enum / имя стратегии (без учёта регистра) / None (SINGLE) к стратегии. """
        if value is None:
            return cls.SINGLE
        if isinstance(value, cls):
            return value
        name = value.name if isinstance(value, Enum) else value
        if isinstance(name, str):
            try:
                return cls[name.strip().upper()]
            except KeyError:
                pass
        raise ValueError(f"Unknown profile switcher strategy: {value!r}")


class ProfileNames(str, Enum):
    """ Предопределённые имена профилей (можно использовать и произвольные строки). """
    DEFAULT = "default"
    SINGLE = "single"
    EMPTY_THEN_FILL = "empty_then_fill"
    FULL_FIRST = "full_first"

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._value2member_map_
