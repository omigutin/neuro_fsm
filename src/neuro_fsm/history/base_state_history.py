__all__ = ['BaseStateHistory']

from abc import ABC
from collections import deque
from typing import Deque, Iterator

from ..config_profiles.state_profiles import StatesProfileConfig
from ..models import StateMeta


class BaseStateHistory(ABC):
    """ Базовый класс истории состояний. """

    def __init__(self, max_len: int = 100) -> None:
        self._states: Deque[StateMeta] = deque(maxlen=max_len)

    def add(self, *states: StateMeta) -> None:
        """ Добавляет состояние в историю. """
        self._states.extend(states)

    def reset(self) -> None:
        """Очищает историю."""
        self._states.clear()

    def __len__(self) -> int:
        return len(self._states)

    def __getitem__(self, idx: int) -> StateMeta:
        return self._states[idx]

    def __iter__(self) -> Iterator[StateMeta]:
        return iter(self._states)

    def __repr__(self) -> str:
        return f"<StateHistory len={len(self._states)}>"
