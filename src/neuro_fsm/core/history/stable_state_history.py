__all__ = ['StableStateHistory']

from ...configs import ProfileConfig
from ..states import StateTupleTuple, State
from .base_state_history import BaseStateHistory


class StableStateHistory(BaseStateHistory):
    """
        Хранит историю стабильных состояний и проверяет,
        соответствует ли она одной из ожидаемых последовательностей.
    """

    def __init__(self, expected_sequences: StateTupleTuple, max_len: int = 100) -> None:
        """
            Args:
                config (ProfileConfig): Конфигурация профиля с init_states и expected_sequences.
                max_len (int): Максимальная длина истории.
        """
        super().__init__(max_len)
        self._expected_sequences: StateTupleTuple = expected_sequences
        self._history_min_len: int = min(len(seq) for seq in self._expected_sequences)

    @property
    def records(self) -> list[State]:
        return list(self._records)

    def last(self) -> State | None:
        """ Возвращает последнее состояние (если есть). """
        return self._records[-1] if self._records else None

    def is_different_from_last(self, *states: State) -> bool:
        """
            Проверяет, отличается ли новая последовательность состояний от последней части истории.
            Returns:
                True - если последовательность отличается.
        """
        history_tail = list(self._records)[-len(states):]
        return any(h.cls_id != s.cls_id for h, s in zip(history_tail, states))

    def is_valid(self) -> bool:
        """
            Проверяет, завершена ли история ожидаемой последовательностью.
            Returns:
                True — если есть полное совпадение с одним из шаблонов.
        """
        if len(self._records) < self._history_min_len:
            return False

        for expected_seq in self._expected_sequences:
            if len(expected_seq) > len(self._records):
                continue

            history_slice = list(self._records)[-len(expected_seq):]
            if all(h.name == e.name for h, e in zip(history_slice, expected_seq)):
                return True

        return False

    def is_impossible(self) -> bool:
        """ Возвращает True, если история больше не может соответствовать ни одной ожидаемой последовательности. """
        for expected_seq in self._expected_sequences:
            if len(expected_seq) > len(self._records):
                continue
            history_tail = list(self._records)[-len(expected_seq):]
            if all(h.cls_id == e.cls_id for h, e in zip(history_tail, expected_seq)):
                return False  # ещё возможен матч
        return True

    def as_dict(self) -> dict:
        """ Сериализует только текущую историю состояний. """
        return {"records": [state.to_dict() for state in self._records]}
