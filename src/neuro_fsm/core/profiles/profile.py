__all__ = ['Profile', 'ProfileDict']

from typing import TypeAlias, Tuple, Dict

from ..states import State, StateTuple, StateDict
from ..counters import StableStateCounters
from ..history import StableStateHistory
from .profile_names import ProfileNames

class Profile:
    """
        Рабочая единица профиля в машине состояний.
        Содержит:
            - Ссылки на State (states, init_states, default_states, expected_sequences)
            - Счётчики состояний
            - Историю состояний
    """
    def __init__(self,
                name: ProfileNames,
                states: StateDict,
                init_states: StateTuple,
                default_states: StateTuple,
                expected_sequences: Tuple[StateTuple, ...],
                description: str = ""
                ) -> None:
        self._name: ProfileNames  = name
        self._description: str = description

        self._states: StateDict = states  # dict[cls_id, State]
        self._init_states: StateTuple = init_states
        self._default_states: StateTuple = default_states

        self._counters = StableStateCounters(states)
        self._history = StableStateHistory(expected_sequences)
        self._history.add(*self._init_states)

    def get_state(self, cls_id: int) -> State:
        return self._states[cls_id]

    @property
    def name(self) -> ProfileNames:
        return self._name

    @property
    def init_states(self) -> StateTuple:
        return self._init_states

    @property
    def default_states(self) -> StateTuple:
        return self._default_states

    @property
    def history(self) -> StableStateHistory:
        return self._history

    def is_reset_trigger(self, cls_id: int) -> bool:
        return self._states[cls_id].is_resetter

    def reset_resettable(self) -> None:
        for state in self._states.values():
            if state.is_resettable:
                self._counters.reset(state.cls_id)

    def reset_resettable_except(self, *cls_ids: int) -> None:
        for state in self._states.values():
            if state.cls_id not in [cls_ids] and state.is_resettable:
                self._counters.reset(state.cls_id)

    def reset_all_states(self) -> None:
        for state in self._states.values():
            self._counters.reset(state.cls_id)

    def is_break_trigger(self, cls_id: int) -> bool:
        return self._states[cls_id].is_breaker

    def is_stable(self, cls_id: int) -> bool:
        """ Проверяет, является ли состояние стабильным (набрало ли нужное кол-во кадров) """
        return self._states[cls_id].stable_min_lim == self._counters.get(cls_id)

    def update(self, cls_id: int) -> None:
        count = self._counters.increment(cls_id)
        state = self.get_state(cls_id)
        if self._should_add_to_history(state, count):
            self._history.add(state)

    def is_expected_seq_valid(self) -> bool:
        return self._history.is_valid()

    def reset(self) -> None:
        self._counters.reset_all()
        self._history.reset()
        self._history.add(*self._init_states)

    def _should_add_to_history(self, state: State, count: int) -> bool:
        return self._history.is_different_from_last(state) and count >= state.stable_min_lim

    def __repr__(self):
        return f"<Profile {self._name} ({len(self._states)} states)>"

ProfileDict: TypeAlias = Dict[ProfileNames, Profile]
