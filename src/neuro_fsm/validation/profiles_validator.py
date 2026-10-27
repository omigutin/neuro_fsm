from __future__ import annotations

__all__ = ["ProfilesValidator"]

from typing import Optional, final

from ..configs import ProfileConfig
from ..models import ProfileSwitcherStrategies


@final
class ProfilesValidator:
    """ Проверки профилей: наличие, профиль по умолчанию, init/default состояния, внешние id. """

    __slots__ = ()

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def validate(
        profiles: dict[str, ProfileConfig],
        def_profile_name: Optional[str],
        strategy: ProfileSwitcherStrategies,
    ) -> None:
        """ Проверки профилей (композит). """
        if not profiles:
            raise ValueError("No profiles defined. Add at least one profile.")
        if def_profile_name is None or def_profile_name not in profiles:
            raise ValueError(f"Default profile {def_profile_name!r} is not present among profiles.")
        for name, profile in profiles.items():
            if name != profile.name:
                raise ValueError(f"Profile key {name!r} differs from profile name {profile.name!r}.")
            ProfilesValidator._validate_init_default(profile)
        if strategy == ProfileSwitcherStrategies.BY_MAPPED_ID:
            ProfilesValidator._validate_mapped_ids(profiles)

    @staticmethod
    def _validate_init_default(profile: ProfileConfig) -> None:
        """ Стартовые состояния обязательны; init/default должны быть состояниями профиля. """
        if not profile.states:
            raise ValueError(f"Profile '{profile.name}' has no states.")
        if not profile.init_states:
            raise ValueError(f"Profile '{profile.name}' has no init states.")
        for kind, states in (("init", profile.init_states), ("default", profile.default_states)):
            for state in states:
                if profile.states.get(state.cls_id) != state:
                    raise ValueError(
                        f"Profile '{profile.name}': {kind} state {state} is not a state of this profile."
                    )

    @staticmethod
    def _validate_mapped_ids(profiles: dict[str, ProfileConfig]) -> None:
        """
            Для BY_MAPPED_ID: хотя бы у одного профиля есть id, id уникальны между профилями.
            Незнакомые id обслуживает профиль по умолчанию.
        """
        if not any(p.mapped_ids for p in profiles.values()):
            raise ValueError("Switcher strategy is BY_MAPPED_ID, but no profile has mapped IDs.")
        seen: dict[int, str] = {}
        for name, profile in profiles.items():
            for pid in profile.mapped_ids:
                if pid in seen:
                    raise ValueError(f"Duplicate mapped id {pid} in profiles '{seen[pid]}' and '{name}'.")
                seen[pid] = name
