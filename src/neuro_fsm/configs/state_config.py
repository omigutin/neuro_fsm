from __future__ import annotations

__all__ = ['StateConfig', 'StateConfigOrIdType', 'StateConfigDict', 'StateConfigTuple', 'StateConfigTupleTuple']

from dataclasses import dataclass
from typing import TypeAlias, Union, Optional


@dataclass(frozen=True, slots=True)
class StateConfig:
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
    fiction: bool = False
    stable_min_lim: Optional[int] = None
    resettable: bool = False
    reset_trigger: bool = False
    break_trigger: bool = False
    threshold: Optional[float] = None

    def __str__(self) -> str:
        """ Краткое строковое представление состояния. """
        return f"<State {self.name} (id={self.cls_id})>"

    def __repr__(self) -> str:
        """ Подробное строковое представление для отладки. """
        return f"State(name={self.name!r}, cls_id={self.cls_id}, full_name={self.full_name!r})"


StateConfigOrIdType: TypeAlias = Union[StateConfig, int]
StateConfigDict: TypeAlias = dict[int, StateConfig]
StateConfigTuple: TypeAlias = tuple[StateConfig, ...]
StateConfigTupleTuple: TypeAlias = tuple[tuple[StateConfig, ...], ...]
