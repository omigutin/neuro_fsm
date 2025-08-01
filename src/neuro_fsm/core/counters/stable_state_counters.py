from __future__ import annotations

__all__ = ['StableStateCounters', 'CountersDict']

from typing import TypeAlias

from ...core.states import StateDict


class StableStateCounters:
    """
        Хранит счётчики повторений состояний по cls_id.
        Работает только с конфигурацией состояний, нужной для логики сброса.
    """

    def __init__(self, states: StateDict):
        self._counters: CountersDict = {cls_id: 0 for cls_id in states}

    def increment(self, cls_id: int) -> int:
        """ Увеличивает счётчик состояния и возвращает новое значение. """
        self._counters[cls_id] += 1
        return self._counters[cls_id]

    def reset_all(self) -> None:
        """ Сбрасывает счётчики всех состояний. """
        for cls_id in self._counters:
            self.reset(cls_id)

    def reset_all_except(self, *cls_ids: int) -> None:
        """ Сбрасывает все счётчики, кроме указанных состояний. """
        for cls_id in self._counters:
            if cls_id not in cls_ids:
                self.reset(cls_id)

    def get(self, cls_id: int) -> int:
        """ Возвращает текущее значение счётчика состояния. """
        return self._counters.get(cls_id, 0)

    def as_dict(self) -> CountersDict:
        """Возвращает копию всех счётчиков."""
        return self._counters.copy()

    def reset(self, cls_id: int) -> None:
        """ Метод сброса счётчика cls_id. """
        self._counters[cls_id] = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(counters={self._counters})"

CountersDict: TypeAlias = dict[int, int]
