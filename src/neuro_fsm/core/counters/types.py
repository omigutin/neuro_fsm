from __future__ import annotations

__all__ = ["CountersDict", ]

from typing import TypeAlias


StateId: TypeAlias = int
CountersDict: TypeAlias = dict[StateId, int]
