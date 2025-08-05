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
    full_name: Optional[str] = None
    fiction: Optional[bool] = None
    alias_of: Optional[int] = None
    stable_min_lim: Optional[int] = None
    resettable: Optional[bool] = None
    reset_trigger: Optional[bool] = None
    break_trigger: Optional[bool] = None
    threshold: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'cls_id': self.cls_id,
            'name': self.name,
            'full_name': self.full_name,
            'fiction': self.fiction,
            'alias_of': self.alias_of,
            'stable_min_lim': self.stable_min_lim,
            'resettable': self.resettable,
            'reset_trigger': self.reset_trigger,
            'break_trigger': self.break_trigger,
            'threshold': self.threshold,
        }

    def __post_init__(self):
        """ Проверяет корректность значений параметров  """
        if len(self.name) == 0:
            raise ValueError(f"[{__class__.__name__}] name must not be empty")
        if self.stable_min_lim is not None and self.stable_min_lim < -1:
            raise ValueError(f"[{__class__.__name__}] stable_min_lim must be >= 0 or None, got {self.stable_min_lim}")
        if self.threshold is not None and not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"[{__class__.__name__}] threshold must be in range [0.0, 1.0], got {self.threshold}")

    def __str__(self) -> str:
        """ Краткое строковое представление состояния. """
        return f"<StateConfig {self.name} (id={self.cls_id})>"

    def __repr__(self) -> str:
        """ Подробное строковое представление для отладки. """
        return f"StateConfig (name={self.name!r}, cls_id={self.cls_id}, full_name={self.full_name!r})"


StateConfigOrIdType: TypeAlias = Union[StateConfig, int]
StateConfigDict: TypeAlias = dict[int, StateConfig]
StateConfigTuple: TypeAlias = tuple[StateConfig, ...]
StateConfigTupleTuple: TypeAlias = tuple[tuple[StateConfig, ...], ...]
