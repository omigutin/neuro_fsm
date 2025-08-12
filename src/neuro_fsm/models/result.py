__all__ = ['FsmResult']

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.states import State, StateTuple

@dataclass(frozen=True, slots=True)
class FsmResult:
    """
        Результат обработки одного такта (кадра) машиной состояний.
        Модель данных — «снимок фактов», без доступа к внутренним объектам FSM.
        Используется для логирования, телеметрии и принятия внешних решений
        (UI/ивенты/метрики), не раскрывая внутреннюю структуру профилей.
        Args:
            active_profile (str):
                Имя активного профиля ПОСЛЕ обработки шага.
            prev_profile (Optional[str]):
                Имя профиля ДО шага, если в ходе шага произошёл переключатель профиля.
                None — если переключения не было.
            state (State):
                Текущее стабильное состояние по завершении шага.
            resetter (bool):
                Флаг: текущее состояние является reset-триггером (инициирует сброс
                счётчиков/истории по правилам профиля).
            breaker (bool):
                Флаг: текущее состояние является «прерывателем» (останавливает
                дальнейшую обработку/классификацию на этом шаге).
            stable (bool):
                Флаг: достигнут ли порог стабильности для текущего состояния
                (счётчик >= stable_min_lim).
            stage_done (bool):
                Флаг: завершена ли ожидаемая последовательность состояний (match
                одной из expected_sequences профиля).
            profile_changed (bool):
                Факт переключения профиля ВО ВРЕМЯ этого шага.
            counters (dict[State, int]):
                Снимок счётчиков по состояниям на момент завершения шага.
                Ключ — объект State (иммутабелен), значение — текущий счётчик.
            history (StateTuple):
                Снимок стабильной истории состояний (последовательность State).
        Замечания:
            - Класс — неизменяемый (frozen=True): после публикации результата он
              не должен меняться.
            - Поля отражают факты шага, а не предоставляют доступ к профилям/менеджерам.
            - Поля state, counters, history содержат прямые объекты доменной модели, а не сериализованные структуры.
              Для сериализации используйте их метод as_dict() или конвертируйте вручную.
    """
    active_profile: str
    prev_profile: Optional[str]
    state: 'State'
    resetter: bool
    breaker: bool
    stable: bool
    stage_done: bool
    profile_changed: bool
    counters: dict[State, int]
    history: StateTuple

    def to_dict(self) -> dict:
        return {
            "active_profile": self.active_profile,
            "prev_profile": self.prev_profile,
            "state": self.state,
            "resetter": self.resetter,
            "breaker": self.breaker,
            "stable": self.stable,
            "stage_done": self.stage_done,
            "profile_changed": self.profile_changed,
            "counters": self.counters,
            "history": self.history,
        }
