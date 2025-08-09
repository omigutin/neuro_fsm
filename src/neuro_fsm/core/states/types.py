from __future__ import annotations

__all__ = ["StateId", "StateDict", "StateTuple", "StateTupleTuple"]

from typing import TypeAlias

from .state import State


StateId: TypeAlias = int
StateDict: TypeAlias = dict[StateId, State]
StateTuple: TypeAlias = tuple[State, ...]
StateTupleTuple: TypeAlias = tuple[StateTuple, ...]
