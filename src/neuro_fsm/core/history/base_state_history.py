__all__ = ['BaseStateHistory']

from abc import ABC
from collections import deque
from typing import Deque, Iterator

from ..states import State


class BaseStateHistory(ABC):
    """ Базовый класс истории состояний. """

    def __init__(self, max_len: int = 100) -> None:
        self._records: Deque[State] = deque(maxlen=max_len)

    def add(self, *states: State) -> None:
        """ Добавляет состояние в историю. """
        self._records.extend(states)

    def clear(self) -> None:
        """Очищает историю."""
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, idx: int) -> State:
        return self._records[idx]

    def __iter__(self) -> Iterator[State]:
        return iter(self._records)

    def __repr__(self) -> str:
        return f"<StateHistory len={len(self._records)}>"
