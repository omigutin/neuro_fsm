__all__ = ['ProfileManager']

from typing import Iterator

from ...configs import ProfileConfigTuple, ProfileConfig
from ..states import State, StateDict
from .profile_switcher import StateProfilesSwitcher
from .profile import Profile, ProfileDict
from ...models import ProfileSwitcherStrategies, ProfileNames


class ProfileManager:
    """
        Менеджер всех профилей машины состояний.
        Хранит активный профиль и управляет логикой обновления/сброса.
    """

    def __init__(self,
                 configs: ProfileConfigTuple,
                 switcher_strategy: ProfileSwitcherStrategies,
                 def_profile: str,
                 states: StateDict
                 ) -> None:
        self._profiles: ProfileDict = self._build_profiles(configs, states)
        if not self._profiles:
            raise ValueError("No profiles initialized in StateProfilesManager")
        self._def_profile: str = def_profile
        self._active_profile: Profile = self._profiles[def_profile]
        self._switcher: StateProfilesSwitcher = StateProfilesSwitcher(strategy=switcher_strategy)

    @property
    def profiles(self) -> ProfileDict:
        return self._profiles

    @property
    def active_profile(self) -> Profile:
        return self._active_profile

    def update_profiles(self, state: State) -> bool:
        """Обновляет профили и возвращает True, если активный профиль сменился."""
        for profile in self._profiles.values():
            profile.update(state)
        return self._set_active_profile()

    def reset_profiles(self) -> None:
        for profile in self._profiles.values():
            profile.reset()
        self._active_profile = self._profiles[self._def_profile]

    @staticmethod
    def _build_profiles(configs: ProfileConfigTuple, states: StateDict) -> ProfileDict:
        """ Создаёт словарь профилей с маппингом ссылок на State """
        profiles: ProfileDict = {}
        for cfg in configs:
            profiles[cfg.name] = ProfileManager._build_profile(cfg, states)
        return profiles

    @staticmethod
    def _build_profile(profile_cfg: ProfileConfig, states: StateDict) -> Profile:
        """ Для одного профиля создаёт структуру со ссылками на State """
        # Мапим статусы профиля на глобальные State
        states_dict = {c.cls_id: states[c.cls_id] for c in profile_cfg.states.values()}
        init_states = tuple(states[c.cls_id] for c in profile_cfg.init_states)
        default_states = tuple(states[c.cls_id] for c in profile_cfg.default_states)
        expected_sequences = tuple(
            tuple(states[c.cls_id] for c in seq) for seq in profile_cfg.expected_sequences
        )
        return Profile(
            name=profile_cfg.name,
            states=states_dict,
            init_states=init_states,
            default_states=default_states,
            expected_sequences=expected_sequences,
        )

    def _set_active_profile(self) -> bool:
        profile = self._switcher.choose_valid(self._profiles)
        if profile and profile != self._active_profile:
            self._active_profile = profile
            # Надо пересчитать сырую историю по правилам нового профиля
            return True
        return False

    def __getitem__(self, key: str | ProfileNames) -> Profile:
        if isinstance(key, ProfileNames):
            return self._profiles[key]
        return next((p for k, p in self._profiles.items() if str(k).lower() == key.lower()), None)

    def __iter__(self) -> Iterator[Profile]:
        return iter(self._profiles.values())

    def __len__(self) -> int:
        return len(self._profiles)
