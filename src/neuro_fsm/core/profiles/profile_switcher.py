__all__ = ['ProfileSwitcher']

from enum import Enum
from typing import Optional, Union

from ...models import ProfileSwitcherStrategies
from ...utils.type_normalizer import TypeNormalizer
from .profile import Profile
from .types import ProfileDict


class ProfileSwitcher:
    """
        Выбор профиля:
            - вручную: по имени или по внешнему id (незнакомый id → профиль по умолчанию);
            - автоматически по стратегии:
                SINGLE, BY_MAPPED_ID — автоматического переключения нет;
                BY_MATCH — профиль, история которого завершилась ожидаемой последовательностью;
                BY_EXCLUSION — единственный профиль, у которого последовательность ещё возможна;
                MIXED — сначала BY_MATCH, затем BY_EXCLUSION.
    """

    def __init__(self, strategy: ProfileSwitcherStrategies, profiles: ProfileDict, def_profile: str) -> None:
        if def_profile not in profiles:
            raise ValueError(f"[ProfileSwitcher] Default profile {def_profile!r} not found")
        self._strategy: ProfileSwitcherStrategies = strategy
        self._profiles: ProfileDict = profiles
        self._def_profile: str = def_profile
        self._id2profile: dict[int, str] = {}

    @property
    def strategy(self) -> ProfileSwitcherStrategies:
        return self._strategy

    def set_profile_ids_mapping(self, profile_ids_map: dict[str, tuple[int, ...]]) -> None:
        """ Устанавливает соответствие имя профиля → внешние id. """
        id2profile: dict[int, str] = {}
        for profile_name, ids in profile_ids_map.items():
            if profile_name not in self._profiles:
                raise ValueError(f"[ProfileSwitcher] Unknown profile {profile_name!r} in ids map")
            for pid in ids:
                if pid in id2profile:
                    raise ValueError(f"[ProfileSwitcher] Duplicate mapped id {pid}")
                id2profile[pid] = profile_name
        self._id2profile = id2profile

    def choose_valid_profile(self, active_profile: Profile) -> Optional[Profile]:
        """ Профиль для автоматического переключения или None, если переключаться не нужно. """
        if self._strategy in (ProfileSwitcherStrategies.SINGLE, ProfileSwitcherStrategies.BY_MAPPED_ID):
            return None
        if self._strategy == ProfileSwitcherStrategies.BY_MATCH:
            return self._choose_by_match(active_profile)
        if self._strategy == ProfileSwitcherStrategies.BY_EXCLUSION:
            return self._choose_by_exclusion(active_profile)
        if self._strategy == ProfileSwitcherStrategies.MIXED:
            return self._choose_by_match(active_profile) or self._choose_by_exclusion(active_profile)
        raise ValueError(f"[ProfileSwitcher] Unknown strategy: {self._strategy}")

    def choose_by_profile_name(self, profile_name: Union[str, Enum]) -> Profile:
        """ Профиль по имени (без учёта регистра). """
        name = TypeNormalizer.normalize_to_str_name(profile_name, case="lower")
        profile = self._profiles.get(name)
        if profile is None:
            raise ValueError(f"[ProfileSwitcher] Unknown profile {name!r}. Available: {list(self._profiles)}")
        return profile

    def choose_by_mapped_id(self, pid: Optional[int]) -> Profile:
        """ Профиль по внешнему id; для None и незнакомых id — профиль по умолчанию. """
        name = self._id2profile.get(pid, self._def_profile) if pid is not None else self._def_profile
        return self._profiles[name]

    def _choose_by_match(self, active_profile: Profile) -> Optional[Profile]:
        """ Первый неактивный профиль, завершивший ожидаемую последовательность. """
        if active_profile.is_expected_seq_valid():
            return None
        return next(
            (p for p in self._profiles.values() if p is not active_profile and p.is_expected_seq_valid()),
            None
        )

    def _choose_by_exclusion(self, active_profile: Profile) -> Optional[Profile]:
        """ Единственный профиль, у которого последовательность ещё возможна. """
        candidates = [p for p in self._profiles.values() if p.is_expected_seq_possible()]
        if len(candidates) == 1 and candidates[0] is not active_profile:
            return candidates[0]
        return None
