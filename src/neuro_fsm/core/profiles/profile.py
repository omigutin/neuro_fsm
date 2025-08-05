__all__ = ['Profile', 'ProfileDict']

from typing import TypeAlias, Tuple, Dict, Optional

from ..states import State, StateTuple, StateDict
from ..counters import StableStateCounters
from ..history import StableStateHistory

class Profile:
    """
        Рабочая единица профиля в машине состояний.
        Содержит:
            - Ссылки на State (states, init_states, default_states, expected_sequences)
            - Счётчики состояний
            - Историю состояний
    """
    def __init__(
            self,
            name: str,
            states: StateDict,
            init_states: StateTuple,
            default_states: StateTuple,
            expected_sequences: Tuple[StateTuple, ...],
            description: str = ""
        ) -> None:
        self._name: str  = name
        self._description: str = description

        self._states: StateDict = states  # dict[cls_id, State]
        self._init_states: StateTuple = init_states
        self._default_states: StateTuple = default_states
        self._cur_state: Optional[State] = self._init_states[-1]

        self._counters = StableStateCounters(states)
        self._history = StableStateHistory(expected_sequences)
        self.add_init_states_to_history()

    def activate_state_by_id(self, cls_id: int) -> State:
        self._cur_state = self._states[cls_id]
        return self._cur_state

    def increment_counter(self) -> None:
        self._counters.increment(self._cur_state.cls_id)

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_resetter(self) -> bool:
        return self._cur_state.is_resetter

    @property
    def is_breaker(self) -> bool:
        return self._cur_state.is_breaker

    @property
    def is_stable(self) -> bool:
        return self._counters.get(self._cur_state.cls_id) >= self._cur_state.stable_min_lim

    def is_expected_seq_valid(self) -> bool:
        return self._history.is_valid()

    def add_init_states_to_history(self) -> None:
        """Добавляет состояния из _init_states в историю, исключая уже присутствующие."""
        existing_ids = {s.cls_id for s in self._history}
        new_states = [s for s in self._init_states if s.cls_id not in existing_ids]
        if new_states:
            self._history.add(*new_states)

    def add_active_state_to_history(self) -> None:
        cur_state_count = self._counters.get(self._cur_state.cls_id)
        if self._history.is_different_from_last(self._cur_state) and cur_state_count >= self._cur_state.stable_min_lim:
            self._history.add(self._cur_state)

    def clear_history(self) -> None:
        self._history.clear()

    def reset_counters(self, only_resettable: bool, except_cur_state: bool) -> None:
        """
            Сбрасывает счётчики состояний, за исключением указанных.
            Args:
                only_resettable (bool): Если True — сбрасываются только состояния с флагом is_resettable.
                                        Если False — сбрасываются все состояния, кроме указанных.
                except_cur_state (bool): Сбрасывать ли счётчик текущего состояния.
        """
        for state in self._states.values():
            is_excepted = except_cur_state and state == self._cur_state
            if not is_excepted and (not only_resettable or state.is_resettable):
                self._counters.reset(state.cls_id)

    def __repr__(self):
        return f"<Profile {self._name} ({len(self._states)} states)>"

ProfileDict: TypeAlias = Dict[str, Profile]
