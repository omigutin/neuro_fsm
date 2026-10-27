from __future__ import annotations

__all__ = ['State']

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class State:
    """
        Рабочее (полностью разрешённое) состояние профиля машины состояний.
        Создаётся StateFactory из StateConfig; параметры приведены к конкретным значениям (порог и alias_of могут быть None).
        stable_min_lim = None — состояние никогда не становится стабильным.
        Равенство и хэш — по паре (cls_id, name): одно и то же состояние в разных профилях
        считается одинаковым, даже если параметры отличаются.
    """

    cls_id: int
    name: str
    full_name: str = ""
    is_fiction: bool = False
    alias_of: Optional[int] = None
    stable_min_lim: Optional[int] = None
    is_resettable: bool = True
    is_resetter: bool = False
    is_breaker: bool = False
    threshold: Optional[float] = None

    def get_base_cls_id(self) -> int:
        """
            Возвращает базовый cls_id для этого состояния.
            Если состояние — алиас, возвращает cls_id оригинального состояния.
        """
        return self.alias_of if self.alias_of is not None else self.cls_id

    @property
    def can_be_stable(self) -> bool:
        """ True, если для состояния задан порог стабильности. """
        return self.stable_min_lim is not None and self.stable_min_lim > 0

    def to_dict(self) -> dict[str, object]:
        """
            Сериализует состояние в словарь.
            Returns:
                dict: Словарь с мета-информацией и параметрами.
        """
        return {
            "name": self.name,
            "cls_id": self.cls_id,
            "full_name": self.full_name,
            "is_fiction": self.is_fiction,
            "alias_of": self.alias_of,
            "stable_min_lim": self.stable_min_lim,
            "is_resettable": self.is_resettable,
            "is_resetter": self.is_resetter,
            "is_breaker": self.is_breaker,
            "threshold": self.threshold
        }

    def describe(self) -> str:
        """ Возвращает строку для UI или логов. """
        return f"{self.name} (id={self.cls_id}) — {self.full_name or 'Без описания'}"

    def __eq__(self, other: object) -> bool:
        """
            Проверяет логическую идентичность двух состояний по имени и ID.
            Поведенческие параметры (params) не сравниваются.
            Args:
                other (State): Другое состояние.

            Returns:
                bool: True, если name и cls_id совпадают.
        """
        if not isinstance(other, State):
            return False
        return self.name == other.name and self.cls_id == other.cls_id

    def __hash__(self) -> int:
        return hash((self.cls_id, self.name))

    def __str__(self) -> str:
        """ Краткое строковое представление состояния. """
        return f"<State {self.name} (id={self.cls_id})>"

    def __repr__(self) -> str:
        """ Подробное строковое представление для отладки. """
        return (f"cls_id={self.cls_id}, name={self.name!r}, full_name={self.full_name!r}, "
                f"is_fiction: {self.is_fiction}, alias_of: {self.alias_of}, stable_min_lim: {self.stable_min_lim}, "
                f"is_resettable: {self.is_resettable}, is_resetter: {self.is_resetter}, is_breaker: {self.is_breaker}, "
                f"threshold: {self.threshold}")
