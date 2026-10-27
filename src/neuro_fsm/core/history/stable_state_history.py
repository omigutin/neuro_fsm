__all__ = ['StableStateHistory']

from ..states import StateTupleTuple, State
from .base_state_history import BaseStateHistory


class StableStateHistory(BaseStateHistory):
    """
        История стабильных состояний профиля.
        Проверяет, завершилась ли она одной из ожидаемых последовательностей и возможно ли ещё совпадение.
        Состояния сравниваются по cls_id.
    """

    def __init__(self, expected_sequences: StateTupleTuple, max_len: int = 100) -> None:
        super().__init__(max_len)
        self._expected_sequences: StateTupleTuple = expected_sequences

    def last(self) -> State | None:
        """ Последнее состояние истории или None. """
        return self._records[-1] if self._records else None

    def is_different_from_last(self, state: State) -> bool:
        """ True, если история пуста или последнее состояние отличается от переданного. """
        return not self._records or self._records[-1].cls_id != state.cls_id

    def is_valid(self) -> bool:
        """ True, если история заканчивается одной из ожидаемых последовательностей. """
        records = self._records
        for expected_seq in self._expected_sequences:
            n = len(expected_seq)
            if n > len(records):
                continue
            tail = list(records)[-n:]
            if all(h.cls_id == e.cls_id for h, e in zip(tail, expected_seq)):
                return True
        return False

    def is_possible(self) -> bool:
        """
            True, если хвост истории совпадает с началом хотя бы одной ожидаемой последовательности,
            то есть последовательность ещё может завершиться.
        """
        records = list(self._records)
        for expected_seq in self._expected_sequences:
            for k in range(min(len(expected_seq), len(records)), 0, -1):
                if all(h.cls_id == e.cls_id for h, e in zip(records[-k:], expected_seq[:k])):
                    return True
        return False

    def is_impossible(self) -> bool:
        """ True, если ни одна ожидаемая последовательность больше не может завершиться. """
        return not self.is_possible()

    def as_dict(self) -> dict[str, list[dict[str, object]]]:
        """ Сериализует текущую историю состояний. """
        return {"records": [state.to_dict() for state in self._records]}
