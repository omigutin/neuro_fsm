from __future__ import annotations

__all__ = ["ActiveProfileView"]

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .profiles.profile_manager import ProfileManager
    from .states.state import State
    from .states.types import StateTuple, StateDict, StateTupleTuple


class ActiveProfileView:
    """
        Read-only фасад активного профиля для внешних потребителей.
        Всегда отражает текущий активный профиль (проксирует через ProfileManager),
        не даёт доступа к методам, меняющим состояние профиля.
    """

    __slots__ = ("_mgr",)
    _mgr: ProfileManager

    def __init__(self, mgr: ProfileManager) -> None:
        object.__setattr__(self, "_mgr", mgr)

    def __setattr__(self, key: str, value: object) -> None:
        raise AttributeError("ActiveProfileView is read-only")

    @property
    def name(self) -> str:
        return self._mgr.active_profile.name

    @property
    def description(self) -> str:
        return self._mgr.active_profile.description

    @property
    def states(self) -> StateDict:
        """ Копия словаря состояний профиля. """
        return dict(self._mgr.active_profile.states)

    @property
    def cur_state(self) -> State:
        return self._mgr.active_profile.cur_state

    @property
    def init_state(self) -> State:
        return self._mgr.active_profile.init_states[-1]

    @property
    def init_states(self) -> StateTuple:
        return self._mgr.active_profile.init_states

    @property
    def default_state(self) -> Optional[State]:
        default_states = self._mgr.active_profile.default_states
        return default_states[-1] if default_states else None

    @property
    def default_states(self) -> StateTuple:
        return self._mgr.active_profile.default_states

    @property
    def expected_sequences(self) -> StateTupleTuple:
        return self._mgr.active_profile.expected_sequences

    @property
    def expected_sequences_names(self) -> tuple[tuple[str, ...], ...]:
        return tuple(tuple(s.name for s in seq) for seq in self._mgr.active_profile.expected_sequences)

    @property
    def counters(self) -> dict[State, int]:
        return self._mgr.active_profile.get_counters()

    @property
    def history(self) -> tuple[State, ...]:
        return self._mgr.active_profile.get_history()

    def get_state(self, cls_id: int) -> Optional[State]:
        return self._mgr.active_profile.states.get(cls_id)

    def get_counter(self, cls_id: int) -> int:
        return self._mgr.active_profile.get_counter_by_cls_id(cls_id)

    def get_threshold(self, cls_id: int) -> Optional[float]:
        state = self.get_state(cls_id)
        return state.threshold if state else None

    def is_breaker(self, cls_id: int) -> bool:
        state = self.get_state(cls_id)
        return state.is_breaker if state else False

    def is_resetter(self, cls_id: int) -> bool:
        state = self.get_state(cls_id)
        return state.is_resetter if state else False

    def is_resettable(self, cls_id: int) -> bool:
        state = self.get_state(cls_id)
        return state.is_resettable if state else False

    def __repr__(self) -> str:
        return f"<ActiveProfileView {self.name}>"
