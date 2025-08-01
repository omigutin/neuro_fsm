__all__ = ['FsmResult']

from dataclasses import dataclass
from typing import Optional

from ..core.states import State


@dataclass(frozen=True, slots=True)
class FsmResult:
    """
        Результат обработки одного кадра машиной состояний.
        Args:
            stage_done (bool): Завершён ли этап (например, цикл продукции).
            cur_state (StateMeta): Текущее активное состояние.
            break_search (bool): Нужно ли прервать обработку текущей рабочей зоны.
            stable_state (Optional[State]): Состояние, признанное стабильным (если есть).
            counters (CountersDict): Счётчики кадров для каждого состояния.
            active_profile (Optional[str]): Имя активного профиля (если профиль используется).
            switch_event (Optional[tuple[int, str]]): Событие переключения профиля (номер кадра, имя профиля).
    """
    active_profile: str
    state: State
    resetter: bool
    breaker: bool
    stable: bool
    stage_done: bool
    # counters: 'CountersDict'
    switch_event: Optional[tuple[int, str]] = None
