__all__ = ['StateParams']

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class StateParams:
    """
        Параметры поведения состояния в рамках одного профиля машины состояний.
        Args:
            stable_min_lim (Optional[int]): Минимальное число кадров для признания состояния стабильным.
                                            None = стабильность отключена.
            resettable (bool):              Можно ли вручную сбросить состояние.
            reset_trigger (bool):           Является ли триггером для сброса других состояний.
            break_trigger (bool):           Завершает ли этап обработки.
            threshold (Optional[float]):    Локальный порог уверенности (None = использовать глобальный).
    """

    stable_min_lim: Optional[int] = None
    resettable: bool = False
    reset_trigger: bool = False
    break_trigger: bool = False
    threshold: Optional[float] = None

    @property
    def is_stability_enabled(self) -> bool:
        """
            Проверка включена ли логика устойчивости.
            Returns:
                bool: True, если значение stable_min_lim задано и больше 0.
        """
        return self.stable_min_lim is not None and self.stable_min_lim > 0

    @property
    def is_resettable(self) -> bool:
        """ Можно ли сбрасывать состояние вручную. """
        return self.resettable

    @property
    def is_resetter(self) -> bool:
        """ Служит ли это состояние триггером сброса других. """
        return self.reset_trigger

    @property
    def is_breaker(self) -> bool:
        """ Завершает ли обработку текущей последовательности. """
        return self.break_trigger

    def to_dict(self) -> dict[str, Optional[bool | int | float]]:
        """
            Преобразует параметры состояния в сериализуемый словарь.
                Returns:
                dict: Словарь всех параметров.
        """
        return {
            "stable_min_lim": self.stable_min_lim,
            "resettable": self.resettable,
            "reset_trigger": self.reset_trigger,
            "break_trigger": self.break_trigger,
            "threshold": self.threshold
        }

    def __post_init__(self):
        """
            Проверяет корректность значений параметров.
            - stable_min_lim должен быть None или >= 0.
            - threshold (если задан) должен быть в диапазоне [0.0, 1.0].
        """
        if self.stable_min_lim is not None and self.stable_min_lim < 0:
            raise ValueError(f"[StateParams] stable_min_lim must be >= 0 or None, got {self.stable_min_lim}")
        if self.threshold is not None and not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"[StateParams] threshold must be in range [0.0, 1.0], got {self.threshold}")
