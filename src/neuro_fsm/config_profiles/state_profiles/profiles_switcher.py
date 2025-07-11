__all__ = ['ProfileSwitcherStrategy', 'StateProfilesSwitcher']

from enum import Enum, auto
from typing import Optional

from .states_profile import StatesProfile, StateProfileTuple


class ProfileSwitcherStrategy(Enum):
    """Стратегии переключения профиля."""
    BY_MATCH = auto()          # Если какой-либо профиль завершил последовательность
    BY_EXCLUSION = auto()      # Если все профили, кроме одного, точно невалидны
    MIXED = auto()             # Сначала match, иначе если остался один возможный — активируем


class StateProfilesSwitcher:
    """
        Выбирает активный профиль на основе выбранной стратегии:
        - BY_MATCH: только если сработала последовательность
        - BY_EXCLUSION: если остался только один потенциально валидный
        - MIXED: сначала match, потом — исключение
    """

    def __init__(self, strategy: ProfileSwitcherStrategy = ProfileSwitcherStrategy.MIXED) -> None:
        self._strategy = strategy

    def choose_valid(self, profiles: StateProfileTuple) -> Optional[StatesProfile]:
        if self._strategy == ProfileSwitcherStrategy.BY_MATCH:
            return self._choose_by_match(profiles)
        elif self._strategy == ProfileSwitcherStrategy.BY_EXCLUSION:
            return self._choose_by_exclusion(profiles)
        elif self._strategy == ProfileSwitcherStrategy.MIXED:
            return self._choose_by_match(profiles) or self._choose_by_exclusion(profiles)
        else:
            raise ValueError(f"Unknown switching strategy: {self._strategy}")

    def _choose_by_match(self, profiles: StateProfileTuple) -> Optional[StatesProfile]:
        for profile in profiles:
            if profile.is_expected_seq_valid():
                return profile
        return None

    def _choose_by_exclusion(self, profiles: StateProfileTuple) -> Optional[StatesProfile]:
        candidates = [p for p in profiles if not p.history.is_impossible()]
        return candidates[0] if len(candidates) == 1 else None
