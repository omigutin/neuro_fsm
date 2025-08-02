__all__ = ['FsmResult']

from dataclasses import dataclass
from typing import Optional

from ..core.states import State


@dataclass(frozen=True, slots=True)
class FsmResult:
    """ Результат обработки одного кадра машиной состояний. """
    active_profile: str
    state: State
    resetter: bool
    breaker: bool
    stable: bool
    stage_done: bool
    switch_event: Optional[tuple[int, str]] = None
    # counters: 'CountersDict'
