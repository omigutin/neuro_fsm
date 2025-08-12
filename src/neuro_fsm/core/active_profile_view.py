from __future__ import annotations

__all__ = ["ActiveProfileView"]

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .profiles.profile import Profile
    from .states.state import State
    from .states.types import StateTuple


class ActiveProfileView:
    """
        Read-only фасад активного профиля для внешних потребителей.
        Даёт доступ к настройкам и атрибутам профиля, не раскрывая его реализацию
        и не позволяя мутировать внутренние структуры.
        Назначение:
            - получить пороги/флаги состояний (breaker/resetter/resettable);
            - прочитать дефолтные/инициализационные состояния;
            - читать ожидаемые последовательности в безопасном виде.
        Внимание:
            - Не хранит тяжёлых ссылок, работает поверх переданного Profile.
            - Импорты типов — только под TYPE_CHECKING, чтобы не ломать рантайм.
    """

    def __init__(self, profile: "Profile") -> None:
        self._active_profile = profile

    @property
    def name(self) -> str:
        return self._active_profile.name

    def init_states(self) -> "StateTuple":
        return self._active_profile.init_states

    def default_states(self) -> "StateTuple":
        return self._active_profile.default_states

    def expected_sequences_names(self) -> tuple[tuple[str, ...], ...]:
        return tuple(tuple(s.name for s in seq) for seq in self._active_profile.expected_sequences)

    def get_threshold(self, cls_id: int) -> Optional[float]:
        return self._active_profile.states[cls_id].threshold

    def is_breaker(self, cls_id: int) -> bool:
        return self._active_profile.states[cls_id].is_breaker

    def is_resetter(self, cls_id: int) -> bool:
        return self._active_profile.states[cls_id].is_resetter

    def is_resettable(self, cls_id: int) -> bool:
        return self._active_profile.states[cls_id].is_resettable
