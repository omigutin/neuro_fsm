from __future__ import annotations

__all__ = ["SequencesValidator"]

from typing import final

from ..configs import ProfileConfig


@final
class SequencesValidator:
    """ Проверки ожидаемых последовательностей. """

    __slots__ = ()

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def validate(profiles: dict[str, ProfileConfig]) -> None:
        """ Последовательности непустые и состоят из состояний своего профиля. """
        for name, profile in profiles.items():
            for idx, seq in enumerate(profile.expected_sequences):
                if not seq:
                    raise ValueError(f"Profile '{name}': expected sequence #{idx} is empty.")
                for state in seq:
                    if profile.states.get(state.cls_id) != state:
                        raise ValueError(
                            f"Profile '{name}': expected sequence #{idx} contains foreign state {state}."
                        )
