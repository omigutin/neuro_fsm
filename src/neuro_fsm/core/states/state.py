from __future__ import annotations

__all__ = ['State', 'StateOrIdType', 'StateTuple', 'StateDict', 'StateTupleTuple', 'StatesDictTuple']

from dataclasses import dataclass
from typing import TypeAlias, Union, Optional


@dataclass(frozen=True, slots=True)
class State:
    """
        Класс объединяет описание состояния (StateMeta) и поведенческие параметры (StateParams).
        Используется в профилях машины состояний и хранит:
        — идентификатор состояния,
        — имя и отображаемое описание,
        — логику обработки (сбросы, прерывания и т.д.).
    """

    cls_id: int
    name: str
    full_name: str = ""
    is_fiction: bool = False
    alias_of: Optional[int] = None
    stable_min_lim: int = 0.0
    is_resettable: bool = True
    is_resetter: bool = False
    is_breaker: bool = False
    threshold: float = 0.0

    def get_base_cls_id(self) -> int:
        """
            Возвращает базовый cls_id для этого состояния.
            Если состояние — алиас, возвращает cls_id оригинального состояния.
        """
        return self.alias_of if self.alias_of is not None else self.cls_id

    def to_dict(self) -> dict[str, str | int | dict[str, str | int | float | None]]:
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

    def __eq__(self, other: State) -> bool:
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

    def __str__(self) -> str:
        """ Краткое строковое представление состояния. """
        return f"<State {self.name} (id={self.cls_id})>"


StateDict: TypeAlias = dict[int, State]

StateOrIdType: TypeAlias = Union[State, int]
StateTuple: TypeAlias = tuple[State, ...]
StateTupleTuple: TypeAlias = tuple[StateTuple, ...]
StatesDictTuple: TypeAlias = dict[StateTuple, int]
