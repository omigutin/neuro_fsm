__all__ = ['Profile', 'ProfileTuple']

from typing import TypeAlias

from ...config.profile_config import ProfileConfig
from ..counters import StableStateCounters
from ..states import StateMeta, StateTuple
from ..history import StableStateHistory


class Profile:
    """
        Рабочая единица профиля в машине состояний.
        Хранит историю стабильных состояний, текущий статус,
        счётчики и методы валидации прохождения ожидаемой последовательности.
    """

    def __init__(self, config: ProfileConfig) -> None:
        self._config: ProfileConfig = config
        self._counters: StableStateCounters = StableStateCounters(config.states)
        self._history: StableStateHistory = StableStateHistory(config)

    @property
    def init_states(self) -> StateTuple:
        return self._config.init_states

    @property
    def default_states(self) -> StateTuple:
        return self._config.default_states

    @property
    def history(self) -> StableStateHistory:
        return self._history

    def update(self, state: StateMeta) -> None:
        """
            Обрабатывает новое состояние:
            - увеличивает счётчик для него;
            - добавляет в историю, если оно стабилизировалось;
            - игнорирует, если состояние не входит в профиль.
        """
        if state.cls_id not in self._config.states:
            return

        count = self._counters.increment(state)

        if self._should_add_to_history(state, count):
            self._history.add(state)

    def is_expected_seq_valid(self) -> bool:
        """
            Проверяет, завершена ли история одной из ожидаемых последовательностей.
            Returns:
                True — если последовательность истории соответствует хотя бы одной ожидаемой.
        """
        return self._history.is_valid()

    def reset(self) -> None:
        """ Сбрасывает историю и счётчики. """
        self._counters.reset_all()
        self._history.reset()
        self._history.add(*self._config.init_states)

    def _should_add_to_history(self, state: StateMeta, count: int) -> bool:
        state = self._config.get_state(state.cls_id)
        return (
                self._history.is_different_from_last(state) and
                state.is_stability_enabled and count >= state.stable_min_lim
        )


ProfileTuple: TypeAlias = tuple[Profile, ...]
