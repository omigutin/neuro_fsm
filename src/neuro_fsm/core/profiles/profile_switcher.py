__all__ = ['StateProfilesSwitcher']

from typing import Optional

from ...models import ProfileSwitcherStrategies
from .profile import Profile, ProfileDict


class StateProfilesSwitcher:
    """
        Выбирает активный профиль на основе выбранной стратегии:
        - BY_MATCH: только если сработала последовательность
        - BY_EXCLUSION: если остался только один потенциально валидный
        - MIXED: сначала match, потом — исключение
    """

    def __init__(self, strategy: ProfileSwitcherStrategies) -> None:
        self._strategy = strategy

    def choose_valid(self, profiles: ProfileDict) -> Optional[Profile]:
        if self._strategy == ProfileSwitcherStrategies.MANUAL:
            return self._choose_by_match(profiles)
        if self._strategy == ProfileSwitcherStrategies.BY_MATCH:
            return self._choose_by_match(profiles)
        if self._strategy == ProfileSwitcherStrategies.BY_EXCLUSION:
            return self._choose_by_exclusion(profiles)
        if self._strategy == ProfileSwitcherStrategies.MIXED:
            return self._choose_by_match(profiles) or self._choose_by_exclusion(profiles)
        raise ValueError(f"Unknown switching strategy: {self._strategy}")

    def _choose_by_match(self, profiles: ProfileDict) -> Optional[Profile]:
        for profile in profiles:
            if profile.is_expected_seq_valid():
                return profile
        return None

    def _choose_by_exclusion(self, profiles: ProfileDict) -> Optional[Profile]:
        candidates = [p for p in profiles if not p.history.is_impossible()]
        return candidates[0] if len(candidates) == 1 else None
