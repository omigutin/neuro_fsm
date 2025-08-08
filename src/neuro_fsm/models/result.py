__all__ = ['FsmResult']

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.states import State


@dataclass(frozen=True, slots=True)
class FsmResult:
    """ Результат обработки одного кадра машиной состояний. """
    active_profile: str
    state: 'State'
    resetter: bool
    breaker: bool
    stable: bool
    is_profile_changed: bool
    stage_done: bool
    switch_event: Optional[tuple[int, str]] = None
    # counters: 'CountersDict'

    def to_dict(self) -> dict:
        return {
            "state_id": self.state.cls_id,
            "state_name": self.state.name,
            "resetter": self.resetter,
            "breaker": self.breaker,
            "stable": self.stable,
            "is_profile_changed": self.is_profile_changed,
            "stage_done": self.stage_done,
            "switch_event": self.switch_event,
            "active_profile": self.active_profile,
        }
