from __future__ import annotations

__all__ = ['FsmResult']

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.states import State


@dataclass(frozen=True, slots=True)
class FsmResult:
    """
        Результат обработки одного шага (кадра) машиной состояний — снимок фактов без доступа к внутренностям FSM.
        Поля:
            active_profile: имя активного профиля после шага ("" — FSM выключена);
            prev_profile: имя профиля до смены, если с прошлого шага профиль сменился (автоматически или вручную),
                          иначе None;
            state: текущее состояние активного профиля после шага (None — FSM выключена);
            resetter: текущее состояние — триггер сброса;
            breaker: текущее состояние — триггер прерывания обработки;
            stable: на этом шаге текущее состояние стало стабильным (счётчик достиг stable_min_lim);
            stage_done: на этом шаге завершилась ожидаемая последовательность (цикл засчитан);
            profile_changed: активный профиль сменился с прошлого шага;
            counters: снимок счётчиков активного профиля {State: count};
            history: снимок истории стабильных состояний активного профиля (до сброса после stage_done);
            step_index: номер шага с момента создания/сброса FSM;
            timestamp: время формирования результата.
    """
    active_profile: str
    prev_profile: Optional[str]
    state: Optional[State]
    resetter: bool
    breaker: bool
    stable: bool
    stage_done: bool
    profile_changed: bool
    counters: dict[State, int]
    history: tuple[State, ...]
    step_index: int
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """ Сериализует результат в словарь из простых типов (для логов и телеметрии). """
        return {
            "active_profile": self.active_profile,
            "prev_profile": self.prev_profile,
            "state": self.state.name if self.state else None,
            "cls_id": self.state.cls_id if self.state else None,
            "resetter": self.resetter,
            "breaker": self.breaker,
            "stable": self.stable,
            "stage_done": self.stage_done,
            "profile_changed": self.profile_changed,
            "counters": {state.name: count for state, count in self.counters.items()},
            "history": [state.name for state in self.history],
            "step_index": self.step_index,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def create_empty(cls) -> FsmResult:
        """ Пустой результат для выключенной FSM. """
        return cls(
            active_profile="",
            prev_profile=None,
            state=None,
            resetter=False,
            breaker=False,
            stable=False,
            stage_done=False,
            profile_changed=False,
            counters={},
            history=(),
            step_index=0,
            timestamp=datetime.now(),
        )
