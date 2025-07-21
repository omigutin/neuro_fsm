__all__ = ['StateProfilesManager']

from typing import Iterator, Optional

from ...config.profile_config import ProfileConfig
from ..states import StateMeta
from .profile_switcher import ProfileSwitcherStrategies, StateProfilesSwitcher
from .profile import Profile, ProfileTuple


class StateProfilesManager:
    """
        Менеджер всех профилей машины состояний.
        Хранит активный профиль и управляет логикой обновления/сброса.
    """

    def __init__(
            self,
            configs: tuple[ProfileConfig, ...],
            switcher_strategy: ProfileSwitcherStrategies = ProfileSwitcherStrategies.MIXED
    ) -> None:
        self._profiles: ProfileTuple = tuple(Profile(cfg) for cfg in configs)
        self._active_profile: Optional[Profile] = None
        self._profiles_switcher: StateProfilesSwitcher = StateProfilesSwitcher(strategy=switcher_strategy)

    @property
    def profiles(self) -> ProfileTuple:
        return self._profiles

    @property
    def active_profile(self) -> Optional[Profile]:
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

    def __iter__(self) -> Iterator[Profile]:
        return iter(self._profiles)

    def __len__(self) -> int:
        return len(self._profiles)

    def __getitem__(self, idx: int) -> Profile:
        return self._profiles[idx]
