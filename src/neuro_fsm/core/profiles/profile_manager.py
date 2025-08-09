__all__ = ['ProfileManager']

from typing import Iterator, Optional

from ...configs.profile_config import ProfileConfig, ProfileConfigTuple
from ...configs.state_config import StateConfigDict
from ...models import ProfileSwitcherStrategies, ProfileNames
from ..states import StateFactory
from .profile_switcher import ProfileSwitcher
from .profile import Profile
from .types import ProfileDict


class ProfileManager:
    """
        Менеджер всех профилей машины состояний.
        Хранит активный профиль и управляет логикой обновления/сброса.
    """

    def __init__(
            self,
            state_configs: StateConfigDict,
            profile_configs: ProfileConfigTuple,
            switcher_strategy: ProfileSwitcherStrategies,
            def_profile: str,
            profile_ids_map
    ) -> None:
        self._profiles: ProfileDict = self._build_profiles(state_configs, profile_configs)
        if not self._profiles:
            raise ValueError("No profiles initialized in StateProfilesManager")
        self._def_profile: str = def_profile
        self._active_profile: Profile = self._profiles[def_profile]
        self._prev_active_profile: Profile = self._profiles[def_profile]
        self._switcher: ProfileSwitcher = ProfileSwitcher(switcher_strategy, self._profiles, profile_ids_map)

    @property
    def active_profile(self) -> Profile:
        return self._active_profile

    @property
    def prev_active_profile(self) -> Profile:
        return self._prev_active_profile

    def register_state(self, cls_id: int):
        for profile in self._profiles.values():
            profile.set_cur_state_by_id(cls_id)
            profile.increment_counter()

    def commit_stable_states(self) -> None:
        for profile in self._profiles.values():
            if profile.is_stable:
                profile.add_cur_state_to_history()
                profile.reset_counters(only_resettable=False, except_cur_state=True)

    def reset_by_trigger(self) -> None:
        for profile in self._profiles.values():
            if profile.is_resetter:
                profile.reset_counters(only_resettable=True, except_cur_state=True)

    def switch_profile_by_pid(self, pid: Optional[int]) -> None:
        """ Сменить активный профиль по указанному pid """
        profile = self._switcher.choose_by_mapped_id(pid)
        if profile and profile != self._active_profile:
            self._active_profile = profile

    def switch_profile_by_name(self, profile_name: ProfileNames | str) -> None:
        """ Сменить активный профиль по названию профиля. """
        profile = self._switcher.choose_by_profile_name(profile_name)
        if profile and profile != self._active_profile:
            self._active_profile = profile

    def update_active_profile(self) -> bool:
        """ Определяет надо ли переключать профиль и если надо, то выставляет выбранный профиль активным """
        valid_profile = self._switcher.choose_valid_profile(self._active_profile)
        if valid_profile and valid_profile != self._active_profile:
            self._prev_active_profile = self._profiles[self._active_profile.name]
            self._active_profile = self._profiles[valid_profile.name]
            return True
        return False

    @staticmethod
    def _build_profiles(config_states: StateConfigDict, profile_configs: ProfileConfigTuple) -> ProfileDict:
        """ Создаёт все профили с собственными State-объектами."""
        return {
            profile_config.name: ProfileManager._build_profile(config_states, profile_config)
            for profile_config in profile_configs
        }

    @staticmethod
    def _build_profile(config_states: StateConfigDict, profile_config: ProfileConfig) -> Profile:
        """ Для одного профиля создаёт структуру со ссылками на State """
        state_dict = StateFactory.build(config_states, profile_config)

        # Преобразуем init_states, default_states, expected_sequences к ссылкам на State
        init_states = tuple(state_dict[s.cls_id] for s in profile_config.init_states)
        default_states = tuple(state_dict[s.cls_id] for s in profile_config.default_states)
        expected_sequences = tuple(
            tuple(state_dict[s.cls_id] for s in seq)
            for seq in profile_config.expected_sequences
        )

        return Profile(
            name=profile_config.name,
            states=state_dict,
            init_states=init_states,
            default_states=default_states,
            expected_sequences=expected_sequences,
        )

    def __getitem__(self, key: str | ProfileNames) -> Profile:
        if isinstance(key, ProfileNames):
            return self._profiles[key]
        return next((p for k, p in self._profiles.items() if str(k).lower() == key.lower()), None)

    def __iter__(self) -> Iterator[Profile]:
        return iter(self._profiles.values())

    def __len__(self) -> int:
        return len(self._profiles)
