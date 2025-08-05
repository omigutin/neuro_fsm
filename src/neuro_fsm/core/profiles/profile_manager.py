__all__ = ['ProfileManager']

from typing import Iterator, Optional

from ...configs import ProfileConfigTuple, ProfileConfig, StateConfigDict
from ...models import ProfileSwitcherStrategies, ProfileNames
from ..states import StateFactory
from .profile_switcher import ProfileSwitcher
from .profile import Profile, ProfileDict


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

        self._switcher: ProfileSwitcher = ProfileSwitcher(switcher_strategy, self._profiles, profile_ids_map)

    @property
    def active_profile(self) -> Profile:
        return self._active_profile

    # @property
    # def profiles(self) -> ProfileDict:
    #     return self._profiles

    # def switch_profile(self, pid: int):
    #     """ Переключение профиля """
    #     self._switcher.switch(self._profiles, pid)

    def update_profiles(self, cls_id: int) -> bool:
        """Обновляет профили и возвращает True, если активный профиль сменился."""
        for profile in self._profiles.values():
            profile.add_active_state_to_history(cls_id)

        is_profile_changed = self._autoswitch_profile()
        if is_profile_changed:
            # Надо пересчитать сырую историю по правилам нового профиля
            pass

        return  is_profile_changed

    def reset_profiles(self) -> None:
        for profile in self._profiles.values():
            profile.reset_counters_and_clear_history()
        self._active_profile = self._profiles[self._def_profile]

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

    def _autoswitch_profile(self) -> bool:
        """ Определяет надо ли переключать профиль и если надо, то выставляет выбранный профиль активным """
        profile = self._switcher.choose_valid_profile(self._profiles)
        if profile and profile != self._active_profile:
            self._active_profile = profile
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
        state_dict = StateFactory.build(profile_config.states)

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
