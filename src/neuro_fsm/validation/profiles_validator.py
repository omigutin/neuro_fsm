from __future__ import annotations

__all__ = ["ProfilesValidator"]

from typing import Optional, final

from ..configs import ProfileConfig
from ..models import ProfileSwitcherStrategies


@final
class ProfilesValidator:
    """ Проверки, связанные с профилями: наличие, дефолтный профиль, mapped IDs. """

    __slots__ = ()

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def validate(
        profiles: dict[str, ProfileConfig],
        def_profile_name: Optional[str],
        strategy: Optional[ProfileSwitcherStrategies],
    ) -> None:
        """ Проверки профилей (композит). """
        ProfilesValidator._validate_exist(profiles, def_profile_name)
        ProfilesValidator._validate_mapped_ids(profiles, strategy)

    @staticmethod
    def _validate_exist(profiles: dict[str, ProfileConfig], def_profile_name: Optional[str]) -> None:
        """ Проверяет наличие хотя бы одного профиля и корректность ссылки на дефолтный профиль. """
        if not profiles:
            raise ValueError("No profiles defined. Add at least one ProfileConfig.")
        if def_profile_name is None or def_profile_name not in profiles:
            raise ValueError(f"Default profile {def_profile_name!r} is not present among added profiles.")

    @staticmethod
    def _validate_mapped_ids(profiles: dict[str, ProfileConfig], strategy: Optional[ProfileSwitcherStrategies]) -> None:
        """
            Валидирует внешние ID профилей. Применяется ТОЛЬКО при стратегии BY_MAPPED_ID.
            Правила:
              - При BY_MAPPED_ID:
                  * ID глобально уникальны (сквозь все профили).
                  * Должен существовать хотя бы один профиль с непустыми ID.
                  * Пустых профилей допускается максимум один.
              - При других стратегиях проверка ID не выполняется.
        """
        if strategy != ProfileSwitcherStrategies.BY_MAPPED_ID:
            return

        ids_by_profile = ProfilesValidator._collect_ids_by_profile(profiles)
        ProfilesValidator._ensure_at_least_one_nonempty(ids_by_profile)
        ProfilesValidator._ensure_global_uniqueness(ids_by_profile)
        ProfilesValidator._ensure_single_empty_when_any_nonempty(ids_by_profile)

    @staticmethod
    def _collect_ids_by_profile(profiles: dict[str, ProfileConfig]) -> dict[str, tuple[int, ...]]:
        """
            Собирает карту: имя_профиля -> кортеж ID.
            Ожидается, что ProfileConfig предоставляет get_ids() -> tuple[int, ...].
            Если метода нет — считаем, что ID не заданы (пусто).
        """
        return {
            name: (prof.get_ids() if hasattr(prof, "get_ids") else tuple())
            for name, prof in profiles.items()
        }

    @staticmethod
    def _ensure_at_least_one_nonempty(ids_by_profile: dict[str, tuple[int, ...]]) -> None:
        """ Требует наличие хотя бы одного профиля с непустыми ID при BY_MAPPED_ID. """
        if not any(len(v) > 0 for v in ids_by_profile.values()):
            raise ValueError(
                "Switcher strategy is BY_MAPPED_ID, but no profile has mapped IDs. "
                "Assign IDs to at least one profile."
            )

    @staticmethod
    def _ensure_global_uniqueness(ids_by_profile: dict[str, tuple[int, ...]]) -> None:
        """ Проверяет, что все назначенные ID уникальны между всеми профилями. """
        seen: dict[int, str] = {}
        for pname, ids in ids_by_profile.items():
            for i in ids:
                if i in seen:
                    raise ValueError(
                        f"Duplicate mapped id {i} between profiles '{seen[i]}' and '{pname}'. "
                        "IDs must be globally unique."
                    )
                seen[i] = pname

    @staticmethod
    def _ensure_single_empty_when_any_nonempty(ids_by_profile: dict[str, tuple[int, ...]]) -> None:
        """
            Если есть непустые ID, пустых профилей допускается не более одного.
            Это задаёт однозначный «дефолтный маршрут» для ненайденных ID.
        """
        empty_profiles = [p for p, ids in ids_by_profile.items() if len(ids) == 0]
        if len(empty_profiles) > 1:
            raise ValueError(
                f"More than one profile has empty IDs: {empty_profiles}. "
                "When any profile has mapped IDs, only a single profile is allowed to have empty IDs."
            )
