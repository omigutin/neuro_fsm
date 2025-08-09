__all__ = ['ProfileSwitcher']

from typing import Optional

from ...config_parser.parsing_utils import normalize_enum_str
from ...models import ProfileSwitcherStrategies, ProfileNames
from .profile import Profile
from .types import ProfileDict


class ProfileSwitcher:
    """
        Выбирает активный профиль на основе выбранной стратегии:
        - BY_MATCH: только если сработала последовательность
        - BY_EXCLUSION: если остался только один потенциально валидный
        - MIXED: сначала match, потом — исключение
    """

    def __init__(self, strategy: ProfileSwitcherStrategies, profiles: ProfileDict, profile_ids_map=None) -> None:
        self._strategy: ProfileSwitcherStrategies = strategy
        self._profiles: ProfileDict = profiles
        # Переключение по id. Словарь profile_name → list of ids и дефолтный профиль для неуказанных в карте id
        self._id2profile: dict[int, str] = {}
        self._unmapped_ids_profile: Optional[str] = None
        if profile_ids_map:
            self.set_profile_ids_mapping(profile_ids_map)

    def set_profile_ids_mapping(self, profile_ids_map: dict[str, list[int]]) -> None:
        """
            Устанавливает соответствие: profile_name → list of ids.
            Если список пустой — профиль считается дефолтным.
        """
        self._id2profile.clear()
        self._unmapped_ids_profile = None

        for profile_name, ids in profile_ids_map.items():
            # Единожды выставляем профиль для незнакомых id
            if not self._unmapped_ids_profile and not ids:
                self._unmapped_ids_profile = profile_name
            for pid in ids:
                self._id2profile[pid] = profile_name

        if not self._unmapped_ids_profile:
            raise ValueError(f"[ProfilesSwitcher] Profile for unmapped ids must be defined.")

    def choose_valid_profile(self, active_profile: Profile) -> Optional[Profile]:
        """ Выбор активного профиля по текущей стратегии. """
        if self._strategy == ProfileSwitcherStrategies.SINGLE:
            return None

        # В случае переключения профайлов через pid, смена профиля осуществляется отдельно в полуручном режиме
        if self._strategy == ProfileSwitcherStrategies.BY_MAPPED_ID:
            return None

        if self._strategy == ProfileSwitcherStrategies.BY_MATCH:
            return self._choose_by_match()

        if self._strategy == ProfileSwitcherStrategies.BY_EXCLUSION:
            return self._choose_by_exclusion()

        if self._strategy == ProfileSwitcherStrategies.MIXED:
            return self._choose_by_match() or self._choose_by_exclusion()

        raise ValueError(f"[ProfilesSwitcher] Unknown strategy: {self._strategy}")

    def choose_by_profile_name(self, profile_name: ProfileNames | str) -> Profile:
        profile_name = normalize_enum_str(profile_name, case="lower")
        return self._profiles[profile_name]

    def choose_by_mapped_id(self, pid: Optional[int]) -> Profile:
        return self._profiles[self._get_profile_name_by_id(pid)]

    def _get_profile_name_by_id(self, pid: Optional[int]) -> str:
        """ Возвращает имя профиля по id или дефолт (если задан), иначе None. """
        return self._id2profile.get(pid, self._unmapped_ids_profile)

    def _choose_by_match(self) -> Optional[Profile]:
        for profile in self._profiles.values():
            if profile.is_expected_seq_valid():
                return profile
        return None

    def _choose_by_exclusion(self) -> Optional[Profile]:
        candidates = [profile for profile in self._profiles.values() if not profile.history.is_impossible()]
        return candidates[0] if len(candidates) == 1 else None


