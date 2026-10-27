from __future__ import annotations

__all__ = ["ConfigValidator"]

from typing import Literal, Optional, final

from ..configs import ProfileConfig
from ..models import ProfileSwitcherStrategies
from .profiles_validator import ProfilesValidator
from .states_validator import StatesValidator
from .sequences_validator import SequencesValidator


@final
class ConfigValidator:
    """ Финальные логические проверки собранной FSM-конфигурации. """

    __slots__ = ()

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def run(
        profiles: dict[str, ProfileConfig],
        def_profile_name: Optional[str],
        strategy: ProfileSwitcherStrategies,
        states_mode: Literal["equal", "individual"] = "individual",
    ) -> None:
        """ Запускает все проверки по порядку. Ошибка — ValueError с описанием. """
        ProfilesValidator.validate(profiles, def_profile_name, strategy)
        StatesValidator.validate(profiles, equal_states=states_mode == "equal")
        SequencesValidator.validate(profiles)
