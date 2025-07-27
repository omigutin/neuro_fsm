from __future__ import annotations

__all__ = ['RawStateHistory',
           # 'RawStateItem',
           # 'RawStateSequence'
           ]

from enum import Enum
from typing import TypeAlias, Sequence, Union

from .base_state_history import BaseStateHistory
from ..states import State

# RawStateItem: TypeAlias = Union[int, str, Enum, State]
# RawStateSequence: TypeAlias = Sequence[RawStateItem]


class RawStateHistory(BaseStateHistory):
    """
        Простейшая история всех состояний без логики профилей и стабильности.
        Хранит полную последовательность и предоставляет базовые методы доступа.
    """

    def __init__(self, max_len: int = 100) -> None:
        super().__init__(max_len)

    def last(self) -> State | None:
        """ Возвращает последнее состояние (если есть). """
        return self._states[-1] if self._states else None

    def count_last_repeats(self) -> int:
        """ Возвращает количество подряд идущих повторений последнего состояния. """
        if not self._states:
            return 0
        last = self._states[-1]
        count = 1
        for state in reversed(list(self._states)[:-1]):
            if state.cls_id == last.cls_id:
                count += 1
            else:
                break
        return count

    def as_list(self) -> list[State]:
        """ Возвращает список всех состояний. """
        return list(self._states)
