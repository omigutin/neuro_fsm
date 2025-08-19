__all__ = ['Profile']

from typing import TYPE_CHECKING, Optional

from ..states import State, StateTuple, StateDict, StateTupleTuple
from ..counters import StableStateCounters
from ..history import StableStateHistory

if TYPE_CHECKING:
    from ...history_writer import StableHistoryWriter

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
            expected_sequences: StateTupleTuple,
            description: str = ""
        ) -> None:
        self._name: str  = name
        self._description: str = description

        self._states: StateDict = states  # dict[cls_id, State]
        self._init_states: StateTuple = init_states
        self._default_states: StateTuple = default_states
        self._expected_sequences: StateTupleTuple = expected_sequences
        self._cur_state: State = self._init_states[-1]

        self._counters = StableStateCounters(states)
        self._history = StableStateHistory(expected_sequences)
        self._add_init_states_to_history()

    def set_cur_state_by_id(self, cls_id: int) -> None:
        self._cur_state = self._states[cls_id]

    def increment_counter(self) -> None:
        self._counters.increment(self._cur_state.cls_id)

    @property
    def name(self) -> str:
        return self._name

    @property
    def cur_state(self) -> State:
        return self._cur_state

    @property
    def states(self) -> StateDict:
        return self._states

    @property
    def init_states(self) -> StateTuple:
        return self._init_states

    @property
    def default_states(self) -> StateTuple:
        return self._default_states

    @property
    def expected_sequences(self) -> StateTupleTuple:
        return self._expected_sequences

    def is_cur_state_resetter(self) -> bool:
        return self._cur_state.is_resetter

    def is_cur_state_breaker(self) -> bool:
        return self._cur_state.is_breaker

    def is_state_stable(self, cur_state: Optional[State] = None) -> bool:
        """ Определяет стабильное ли состояние. Если stable_min_lim не задано, то состояние не может быть стабильным """
        state = cur_state if cur_state else self._cur_state
        if state.stable_min_lim and state.stable_min_lim >= 0:
            return self._counters.get(state.cls_id) >= state.stable_min_lim
        else:
            return False

    def get_counter_by_cls_id(self, cls_id: int) -> int:
        """ Возвращает счётчик состояния, найденного по cls_id. """
        return self._counters.get(cls_id)

    def get_counters(self) -> dict[State, int]:
        """ Возвращает словарь {State: count}, что удобно для логирования и отображения. """
        counters = self._counters.as_dict()
        return {self._states[cls_id]: count for cls_id, count in counters.items()}

    def get_history(self) -> list[State]:
        return self._history.records

    def is_expected_seq_valid(self, writer: "StableHistoryWriter") -> bool:
        if self._history.is_valid():
            writer.write_action(
                cur_state=self.cur_state,
                count=self.get_counter_by_cls_id(self.cur_state.cls_id),
                action="expected_seq_done",
                profile=self
            )
            return True
        return False

    def add_cur_state_to_history(self) -> bool:
        cur_state_count = self._counters.get(self._cur_state.cls_id)
        if self._history.is_different_from_last(self._cur_state) and cur_state_count >= self._cur_state.stable_min_lim:
            self._history.add(self._cur_state)
            return True
        return False

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

    def reset_to_init_state(self):
        self.reset_counters(only_resettable=False, except_cur_state=False)
        self._history.clear()
        self._add_init_states_to_history()

    def _add_init_states_to_history(self) -> None:
        """Добавляет состояния из _init_states в историю, исключая уже присутствующие."""
        existing_ids = {s.cls_id for s in self._history}
        new_states = [s for s in self._init_states if s.cls_id not in existing_ids]
        if new_states:
            self._history.add(*new_states)

    def __repr__(self):
        return f"<Profile {self._name} ({len(self._states)} states)>"
