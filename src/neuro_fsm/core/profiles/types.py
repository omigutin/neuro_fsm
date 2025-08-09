from __future__ import annotations

__all__ = ["ProfileId", "ProfileName", "ProfileDict", "ProfileIdsMap", ]

from typing import TypeAlias

from .profile import Profile

ProfileId: TypeAlias = int
ProfileName: TypeAlias = str
ProfileDict: TypeAlias = dict[ProfileName, Profile]
ProfileIdsMap: TypeAlias = dict[ProfileName, tuple[ProfileId, ...]]
