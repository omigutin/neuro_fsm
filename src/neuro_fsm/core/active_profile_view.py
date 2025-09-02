from __future__ import annotations

__all__ = ["ActiveProfileView"]

from typing import Optional, TYPE_CHECKING, Any

from .profiles.profile import Profile

if TYPE_CHECKING:
    from .profiles.profile_manager import ProfileManager
    from .states.state import State
    from .states.types import StateTuple, StateDict


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
            - Не хранит тяжёлых ссылок на профиль; проксирует через ProfileManager к текущему active_profile.
            - Импорты типов — только под TYPE_CHECKING, чтобы не ломать рантайм.
    """

    __slots__ = ("_mgr",)

    def __init__(self, mgr: "ProfileManager") -> None:
        super().__setattr__("_mgr", mgr)

    # Универсальный прокси: любые НЕ найденные атрибуты → к текущему active_profile
    def __getattr__(self, name: str) -> Any:
        return getattr(self._mgr.active_profile, name)

    # Запрещаем мутацию через view
    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("ActiveProfileView is read-only")

    @property
    def name(self) -> str:
        return self._mgr.active_profile.name

    @property
    def states(self) -> "StateDict":
        return self._mgr.active_profile.states

    @property
    def init_state(self) -> "State":
        return self._mgr.active_profile.init_states[-1]

    @property
    def init_states(self) -> "StateTuple":
        return self._mgr.active_profile.init_states

    @property
    def default_state(self) -> "State":
        return self._mgr.active_profile.default_states[-1]

    @property
    def default_states(self) -> "StateTuple":
        return self._mgr.active_profile.default_states

    @property
    def expected_sequences_names(self) -> tuple[tuple[str, ...], ...]:
        ap = self._mgr.active_profile
        return tuple(tuple(s.name for s in seq) for seq in ap.expected_sequences)

    def get_threshold(self, cls_id: int) -> Optional[float]:
        return self._mgr.active_profile.states[cls_id].threshold

    def is_breaker(self, cls_id: int) -> bool:
        return self._mgr.active_profile.states[cls_id].is_breaker

    def is_resetter(self, cls_id: int) -> bool:
        return self._mgr.active_profile.states[cls_id].is_resetter

    def is_resettable(self, cls_id: int) -> bool:
        return self._mgr.active_profile.states[cls_id].is_resettable
