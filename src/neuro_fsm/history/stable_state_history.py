__all__ = ['StableStateHistory']

from .base_state_history import BaseStateHistory
from ..models import State, StatesTupleTuple
from ..config_profiles.state_profiles import StatesProfileConfig


class StableStateHistory(BaseStateHistory):
    """
        Хранит историю стабильных состояний и проверяет,
        соответствует ли она одной из ожидаемых последовательностей.
    """

    def __init__(self, config: StatesProfileConfig, max_len: int = 100) -> None:
        """
            Args:
                config (StatesProfileConfig): Конфигурация профиля с init_states и expected_sequences.
                max_len (int): Максимальная длина истории.
        """
        super().__init__(config, max_len)
        self._expected_sequences: StatesTupleTuple = config.expected_sequences
        self._history_min_len: int = min(len(seq) for seq in self._expected_sequences)
        self._states.extend(config.init_states or [])

    def is_different_from_last(self, *states: State) -> bool:
        """
            Проверяет, отличается ли новая последовательность состояний от последней части истории.
            Returns:
                True - если последовательность отличается.
        """
        history_tail = list(self._states)[-len(states):]
        return any(h.cls_id != s.cls_id for h, s in zip(history_tail, states))

    def is_valid(self) -> bool:
        """
            Проверяет, завершена ли история ожидаемой последовательностью.
            Returns:
                True — если есть полное совпадение с одним из шаблонов.
        """
        if len(self._states) < self._history_min_len:
            return False

        for expected_seq in self._expected_sequences:
            if len(expected_seq) > len(self._states):
                continue

            history_slice = list(self._states)[-len(expected_seq):]
            if all(h.name == e.name for h, e in zip(history_slice, expected_seq)):
                return True

        return False

    def is_impossible(self) -> bool:
        """ Возвращает True, если история больше не может соответствовать ни одной ожидаемой последовательности. """
        for expected_seq in self._expected_sequences:
            if len(expected_seq) > len(self._states):
                continue
            history_tail = list(self._states)[-len(expected_seq):]
            if all(h.cls_id == e.cls_id for h, e in zip(history_tail, expected_seq)):
                return False  # ещё возможен матч
        return True
