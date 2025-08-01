__all__ = ['ProfileByIdRouter']

from typing import Dict, List, Any, Union
from enum import Enum

from ...config_parser.parsing_utils import normalize_enum_str


class ProfileByIdRouter:
    """
        Универсальный роутер профилей по id продукта (или любому другому key).
        Позволяет работать как с Enum, так и с произвольными str-именами профилей.
    """

    def __init__(self, mapping: Dict[Union[str, Enum], List[Any]], default: Union[str, Enum, None] = None):
        """
            mapping: {profile_name: [id1, id2, ...], ...}
            default: имя профиля по умолчанию (str или Enum)
        """
        self._map: Dict[str, set] = {
            normalize_enum_str(profile_name): set(ids)
            for profile_name, ids in mapping.items()
        }
        self._profiles = list(self._map.keys())
        self._default = normalize_enum_str(default) if default is not None else None

        # Для быстрого поиска id → profile
        self._id2profile: Dict[Any, str] = {}
        for profile, ids in self._map.items():
            for pid in ids:
                self._id2profile[pid] = profile

    @property
    def profiles(self) -> List[str]:
        """ Возвращает список всех профилей (в normalized-строках). """
        return self._profiles

    def get_profile_by_id(self, pid: Any) -> str:
        """ Возвращает нормализованное имя профиля для id, либо default, либо кидает ошибку. """
        profile = self._id2profile.get(pid)
        if profile:
            return profile
        if self._default:
            return self._default
        raise KeyError(f"Profile for id={pid} not found and no default profile set.")

    def get_profile_ids(self, profile: Union[str, Enum]) -> List[Any]:
        """ Возвращает список id для данного профиля. """
        norm = normalize_enum_str(profile)
        return list(self._map.get(norm, []))

    def set_default(self, profile: Union[str, Enum]):
        """ Устанавливает профиль по умолчанию (строка или Enum). """
        norm = normalize_enum_str(profile)
        if norm not in self._profiles:
            raise ValueError(f"Default profile '{profile}' not in available profiles: {self._profiles}")
        self._default = norm
