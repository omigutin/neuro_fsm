__all__ = ['StateProfilesManager']

from typing import Iterator, Optional

from ...models import StateMeta
from .profiles_switcher import ProfileSwitcherStrategy, StateProfilesSwitcher
from .states_profile_config import StatesProfileConfig
from .states_profile import StatesProfile, StateProfileTuple


class StateProfilesManager:
    """
        Менеджер всех профилей машины состояний.
        Хранит активный профиль и управляет логикой обновления/сброса.
    """

    def __init__(
            self,
            configs: tuple[StatesProfileConfig, ...],
            switcher_strategy: ProfileSwitcherStrategy = ProfileSwitcherStrategy.MIXED
    ) -> None:
        self._profiles: StateProfileTuple = tuple(StatesProfile(cfg) for cfg in configs)
        self._active_profile: Optional[StatesProfile] = None
        self._profiles_switcher: StateProfilesSwitcher = StateProfilesSwitcher(strategy=switcher_strategy)

    @property
    def profiles(self) -> StateProfileTuple:
        return self._profiles

    @property
    def active_profile(self) -> Optional[StatesProfile]:
        return self._active_profile

    def update_profiles(self, state: StateMeta) -> bool:
        """Обновляет профили и возвращает True, если активный профиль сменился."""
        for profile in self._profiles:
            profile.update(state)
        return self._set_active_profile()

    def reset_profiles(self) -> None:
        for profile in self._profiles:
            profile.reset()
        self._active_profile = None

    def _set_active_profile(self) -> bool:
        profile = self._profiles_switcher.choose_valid(self._profiles)
        if profile and profile != self._active_profile:
            self._active_profile = profile
            return True
        return False

    def __iter__(self) -> Iterator[StatesProfile]:
        return iter(self._profiles)

    def __len__(self) -> int:
        return len(self._profiles)

    def __getitem__(self, idx: int) -> StatesProfile:
        return self._profiles[idx]
