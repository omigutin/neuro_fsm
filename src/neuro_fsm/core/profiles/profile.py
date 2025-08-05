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

        self._counters = StableStateCounters(states)
        self._history = StableStateHistory(expected_sequences)
        self._history.add(*self._init_states)

        self._cur_state: Optional[State] = self._init_states[-1]

    def set_cur_state_by_cls_id(self, cls_id: int) -> State:
        self._cur_state = self._states[cls_id]
        return self._cur_state

    def increment_counter(self, cls_id: Optional[int]=None) -> None:
        self._counters.increment(cls_id if cls_id else self._cur_state.cls_id)

    @property
    def name(self) -> str:
        return self._name

    # @property
    # def init_states(self) -> StateTuple:
    #     return self._init_states
    #
    # @property
    # def default_states(self) -> StateTuple:
    #     return self._default_states
    #
    # @property
    # def history(self) -> StableStateHistory:
    #     return self._history

    def is_reset_trigger(self, cls_id: Optional[int]=None) -> bool:
        return self._states[cls_id if cls_id else self._cur_state.cls_id].is_resetter

    def is_break_trigger(self, cls_id: Optional[int]=None) -> bool:
        return self._states[cls_id if cls_id else self._cur_state.cls_id].is_breaker

    def is_state_stable(self, cls_id: Optional[int]=None) -> bool:
        """ Проверяет, является ли состояние стабильным (набрало ли нужное кол-во кадров) """
        if cls_id:
            return self._states[cls_id].stable_min_lim == self._counters.get(cls_id)
        else:
            return self._cur_state.stable_min_lim == self._counters.get(self._cur_state.cls_id)

    def is_expected_seq_valid(self) -> bool:
        return self._history.is_valid()

    def add_to_history(self, cls_id: Optional[int]=None) -> None:
        state = self._states[cls_id] if cls_id else self._cur_state
        if self._should_add_to_history(state, self._counters.get(state.cls_id)):
            self._history.add(state)

    def reset_counters(self, only_resettable: bool, except_cur_state: bool) -> None:
        """
            Сбрасывает счётчики состояний, за исключением указанных.
            Args:
                only_resettable (bool): Если True — сбрасываются только состояния с флагом is_resettable.
                                        Если False — сбрасываются все состояния, кроме указанных.
                except_cur_state (bool): Сбрасывать ли счётчик текущего состояния.
        """
        for state in self._states.values():
            if (except_cur_state and state != self._cur_state) and (not only_resettable or state.is_resettable):
                self._counters.reset(state.cls_id)

    def reset_counters_and_clear_history(self) -> None:
        self._counters.reset_all()
        self._history.clear()
        self._history.add(*self._init_states)

    def _should_add_to_history(self, state: State, count: int) -> bool:
        return self._history.is_different_from_last(state) and count >= state.stable_min_lim

    def __repr__(self):
        return f"<Profile {self._name} ({len(self._states)} states)>"

ProfileDict: TypeAlias = Dict[str, Profile]
