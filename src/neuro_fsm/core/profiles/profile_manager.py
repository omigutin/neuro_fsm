__all__ = ['ProfileManager']

from enum import Enum
from typing import Iterator, Optional, Union

from ...configs.profile_config import ProfileConfig, ProfileConfigTuple
from ...models import ProfileSwitcherStrategies
from ...utils.type_normalizer import TypeNormalizer
from ..states import StateFactory
from .profile_switcher import ProfileSwitcher
from .profile import Profile
from .types import ProfileDict


class ProfileManager:
    """
        Менеджер профилей машины состояний.
        Хранит профили и активный профиль, выполняет общие для всех профилей шаги обработки.
    """

    def __init__(
            self,
            profile_configs: ProfileConfigTuple,
            switcher_strategy: ProfileSwitcherStrategies,
            def_profile: str,
    ) -> None:
        self._profiles: ProfileDict = {cfg.name: self._build_profile(cfg) for cfg in profile_configs}
        if not self._profiles:
            raise ValueError("[ProfileManager] No profiles defined")
        if def_profile not in self._profiles:
            raise ValueError(f"[ProfileManager] Default profile {def_profile!r} not found")
        self._def_profile: str = def_profile
        self._active_profile: Profile = self._profiles[def_profile]
        self._switcher = ProfileSwitcher(switcher_strategy, self._profiles, def_profile)
        self._switcher.set_profile_ids_mapping({cfg.name: cfg.mapped_ids for cfg in profile_configs})

    @property
    def profiles(self) -> ProfileDict:
        return self._profiles

    @property
    def active_profile(self) -> Profile:
        return self._active_profile

    @property
    def default_profile(self) -> Profile:
        return self._profiles[self._def_profile]

    def register_state(self, cls_id: Optional[int]) -> None:
        """ Передаёт входное состояние всем профилям. """
        for profile in self._profiles.values():
            profile.register_state(cls_id)

    def reset_by_trigger(self) -> None:
        """ В профилях, где текущее состояние — триггер сброса, сбрасывает сбрасываемые счётчики. """
        for profile in self._profiles.values():
            if profile.cur_state.is_resetter:
                profile.reset_counters(only_resettable=True, except_cur_state=True)

    def commit_stable_states(self) -> list[Profile]:
        """
            Для профилей, где текущее состояние стало стабильным: добавляет его в историю
            и сбрасывает остальные счётчики.
            Returns:
                Профили, в историю которых добавлено новое состояние.
        """
        added: list[Profile] = []
        for profile in self._profiles.values():
            if profile.is_state_stable():
                if profile.add_cur_state_to_history():
                    added.append(profile)
                profile.reset_counters(only_resettable=False, except_cur_state=True)
        return added

    def reset_all_to_init(self) -> None:
        """ Сбрасывает счётчики и историю всех профилей. """
        for profile in self._profiles.values():
            profile.reset_to_init_state()

    def switch_profile_by_pid(self, pid: Optional[int]) -> bool:
        """ Делает активным профиль по внешнему id. Returns: True, если профиль сменился. """
        return self._set_active(self._switcher.choose_by_mapped_id(pid))

    def switch_profile_by_name(self, profile_name: Union[str, Enum]) -> bool:
        """ Делает активным профиль по имени. Returns: True, если профиль сменился. """
        return self._set_active(self._switcher.choose_by_profile_name(profile_name))

    def update_active_profile(self) -> bool:
        """ Автоматически переключает профиль по стратегии. Returns: True, если профиль сменился. """
        candidate = self._switcher.choose_valid_profile(self._active_profile)
        return self._set_active(candidate) if candidate is not None else False

    def _set_active(self, profile: Profile) -> bool:
        if profile is self._active_profile:
            return False
        self._active_profile = profile
        return True

    @staticmethod
    def _build_profile(profile_config: ProfileConfig) -> Profile:
        """ Создаёт рабочий профиль: State-объекты и ссылки на них в init/default/sequences. """
        states = StateFactory.build(profile_config)
        return Profile(
            name=profile_config.name,
            states=states,
            init_states=tuple(states[s.cls_id] for s in profile_config.init_states),
            default_states=tuple(states[s.cls_id] for s in profile_config.default_states),
            expected_sequences=tuple(
                tuple(states[s.cls_id] for s in seq) for seq in profile_config.expected_sequences
            ),
            description=profile_config.description,
        )

    def __getitem__(self, key: Union[str, Enum]) -> Profile:
        return self._profiles[TypeNormalizer.normalize_to_str_name(key, case="lower")]

    def __iter__(self) -> Iterator[Profile]:
        return iter(self._profiles.values())

    def __len__(self) -> int:
        return len(self._profiles)
