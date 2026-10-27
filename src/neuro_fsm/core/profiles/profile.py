__all__ = ['Profile']

from typing import Optional

from ..states import State, StateTuple, StateDict, StateTupleTuple
from ..counters import StableStateCounters
from ..history import StableStateHistory


class Profile:
    """
        Рабочий профиль машины состояний: состояния, счётчики и история стабильных состояний.
        Все профили FSM получают каждое входное состояние параллельно; результат формирует активный.
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
        if not init_states:
            raise ValueError(f"[Profile] Profile '{name}' must have at least one init state")
        self._name: str = name
        self._description: str = description
        self._states: StateDict = states
        self._init_states: StateTuple = init_states
        self._default_states: StateTuple = default_states
        self._expected_sequences: StateTupleTuple = expected_sequences
        self._cur_state: State = init_states[-1]
        self._counters = StableStateCounters(states)
        self._history = StableStateHistory(expected_sequences)
        self._history.add(*self._unique_init_states())

    # ---------------- свойства ----------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

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

    # ---------------- шаг обработки ----------------

    def resolve_state(self, cls_id: Optional[int]) -> State:
        """
            Возвращает состояние профиля по cls_id.
            Для None или неизвестного cls_id — последнее состояние по умолчанию.
            Raises:
                KeyError: если cls_id неизвестен, а состояния по умолчанию не заданы.
        """
        state = self._states.get(cls_id) if cls_id is not None else None
        if state is not None:
            return state
        if self._default_states:
            return self._default_states[-1]
        raise KeyError(f"Unknown cls_id={cls_id!r} in profile '{self._name}' and no default states defined")

    def register_state(self, cls_id: Optional[int]) -> State:
        """ Делает состояние текущим и увеличивает его счётчик. """
        self._cur_state = self.resolve_state(cls_id)
        self._counters.increment(self._cur_state.cls_id)
        return self._cur_state

    def is_state_stable(self, state: Optional[State] = None) -> bool:
        """ True, если счётчик состояния ровно достиг stable_min_lim (событие стабильности). """
        state = state or self._cur_state
        return state.can_be_stable and self._counters.get(state.cls_id) == state.stable_min_lim

    def add_cur_state_to_history(self) -> bool:
        """ Добавляет текущее состояние в историю, если оно стабильно и отличается от последнего. """
        state = self._cur_state
        if state.stable_min_lim is None or self._counters.get(state.cls_id) < state.stable_min_lim:
            return False
        if not self._history.is_different_from_last(state):
            return False
        self._history.add(state)
        return True

    def is_expected_seq_valid(self) -> bool:
        """ True, если история завершилась одной из ожидаемых последовательностей. """
        return self._history.is_valid()

    def is_expected_seq_possible(self) -> bool:
        """ True, если ожидаемая последовательность ещё может завершиться. """
        return self._history.is_possible()

    # ---------------- счётчики и история ----------------

    def get_counter_by_cls_id(self, cls_id: int) -> int:
        """ Счётчик состояния по cls_id. """
        return self._counters.get(cls_id)

    def get_counters(self) -> dict[State, int]:
        """ Снимок счётчиков {State: count}. """
        return {self._states[cls_id]: count for cls_id, count in self._counters.as_dict().items()}

    def get_history(self) -> tuple[State, ...]:
        """ Снимок истории стабильных состояний. """
        return self._history.records

    def reset_counters(self, only_resettable: bool, except_cur_state: bool) -> None:
        """
            Сбрасывает счётчики состояний.
            Args:
                only_resettable: сбрасывать только состояния с флагом is_resettable.
                except_cur_state: не сбрасывать счётчик текущего состояния.
        """
        for state in self._states.values():
            if except_cur_state and state.cls_id == self._cur_state.cls_id:
                continue
            if only_resettable and not state.is_resettable:
                continue
            self._counters.reset(state.cls_id)

    def reset_to_init_state(self) -> None:
        """ Сбрасывает счётчики и историю к стартовому состоянию. Текущее состояние не меняется. """
        self._counters.reset_all()
        self._history.clear()
        self._history.add(*self._unique_init_states())

    def _unique_init_states(self) -> list[State]:
        """ Стартовые состояния без подряд идущих повторов. """
        result: list[State] = []
        for state in self._init_states:
            if not result or result[-1].cls_id != state.cls_id:
                result.append(state)
        return result

    def __repr__(self) -> str:
        return f"<Profile {self._name} ({len(self._states)} states)>"
