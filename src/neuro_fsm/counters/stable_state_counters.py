__all__ = ['StableStateCounters']

from ..models import StateMeta, CountersDict, StatesDict, StateOrIdType


class StableStateCounters:
    """
        Хранит счётчики повторений состояний по cls_id.
        Работает только с конфигурацией состояний, нужной для логики сброса.
    """

    def __init__(self, state_configs: StatesDict):
        self._state_configs: StatesDict = state_configs
        self._counters: CountersDict = {cls_id: 0 for cls_id in state_configs}

    def increment(self, state: StateMeta) -> int:
        """ Увеличивает счётчик состояния и возвращает новое значение. """
        self._counters[state.cls_id] += 1
        return self._counters[state.cls_id]

    def reset_all(self) -> None:
        """ Сбрасывает счётчики всех состояний. """
        for cls_id in self._counters:
            self._reset(cls_id)

    def reset_all_except(self, *excluded: StateMeta) -> None:
        """ Сбрасывает все счётчики, кроме указанных состояний. """
        excluded_ids = {s.cls_id for s in excluded}
        for cls_id in self._counters:
            if cls_id not in excluded_ids:
                self._reset(cls_id)

    def reset_resettable(self) -> None:
        """ Сбрасывает только resettable-состояния. """
        for cls_id, config in self._state_configs.items():
            if config.resettable:
                self._reset(cls_id)

    def reset_resettable_except(self, *excluded: StateMeta) -> None:
        """ Сбрасывает resettable-состояния, кроме указанных. """
        excluded_ids = {s.cls_id for s in excluded}
        for cls_id, config in self._state_configs.items():
            if config.resettable and cls_id not in excluded_ids:
                self._reset(cls_id)

    def get(self, state: StateMeta) -> int:
        """ Возвращает текущее значение счётчика состояния. """
        return self._counters.get(state.cls_id, 0)

    def as_dict(self) -> CountersDict:
        """Возвращает копию всех счётчиков."""
        return self._counters.copy()

    def _reset(self, state_or_id: StateOrIdType) -> None:
        """ Метод сброса счётчика по состоянию или cls_id. """
        cls_id = state_or_id.cls_id if isinstance(state_or_id, StateMeta) else state_or_id
        self._counters[cls_id] = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(counters={self._counters})"
