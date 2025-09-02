from __future__ import annotations

__all__ = ["SequencesValidator"]

from typing import final

from ..configs import ProfileConfig


@final
class SequencesValidator:
    """
        Проверки ожидаемых последовательностей (будет расширено при добавлении правил).
        Сейчас — заглушка.
    """

    __slots__ = ()

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def validate(profiles: dict[str, ProfileConfig]) -> None:
        """ Место для будущих проверок согласованности EXPECTED_SEQUENCES и т.п. """
        return
