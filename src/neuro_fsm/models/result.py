__all__ = ['StateMachineResult']

from dataclasses import dataclass
from typing import Optional

from .state_meta import StateMeta
from .types import CountersDict


@dataclass(frozen=True, slots=True)
class StateMachineResult:
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
    stage_done: bool
    cur_state: StateMeta

    break_search: bool
    stable_state: Optional[StateMeta]
    counters: CountersDict
    active_profile: Optional[str]
    switch_event: Optional[tuple[int, str]] = None
