from __future__ import annotations

__all__ = ['StateConfig', 'StateConfigId', 'StateConfigOrIdType', 'StateConfigDict', 'StateConfigTuple',
           'StateConfigTupleTuple']

from dataclasses import dataclass
from typing import Optional, TypeAlias, Union


@dataclass(frozen=True, slots=True)
class StateConfig:
    """
        Конфигурация одного состояния (класса нейросети) внутри профиля.
        Поля со значением None означают «не задано»: итоговое значение определяется при создании State
        (см. StateFactory) или наследуется от базового профиля.
        Поля:
            cls_id: идентификатор класса нейросети;
            name: уникальное в пределах профиля имя состояния;
            full_name: описание для логов и UI;
            fiction: состояние искусственное (не выдаётся нейросетью);
            alias_of: cls_id состояния, синонимом которого является данное;
            stable_min_lim: сколько раз подряд (без сброса) должно прийти состояние, чтобы стать стабильным.
                            None или -1 — состояние никогда не становится стабильным;
            resettable: счётчик состояния сбрасывается состояниями-триггерами сброса;
            reset_trigger: состояние сбрасывает счётчики сбрасываемых состояний;
            break_trigger: состояние сигнализирует о прерывании обработки;
            threshold: индивидуальный порог уверенности нейросети для состояния.
    """
    cls_id: int
    name: str
    full_name: Optional[str] = None
    fiction: Optional[bool] = None
    alias_of: Optional[int] = None
    stable_min_lim: Optional[int] = None
    resettable: Optional[bool] = None
    reset_trigger: Optional[bool] = None
    break_trigger: Optional[bool] = None
    threshold: Optional[float] = None

    def __post_init__(self) -> None:
        """ Проверяет корректность значений параметров. """
        if not isinstance(self.cls_id, int) or isinstance(self.cls_id, bool):
            raise TypeError(f"[StateConfig] cls_id must be int, got {self.cls_id!r}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"[StateConfig] name must be a non-empty string, got {self.name!r}")
        if self.stable_min_lim is not None and self.stable_min_lim < -1:
            raise ValueError(f"[StateConfig] stable_min_lim must be >= -1 or None, got {self.stable_min_lim}")
        if self.threshold is not None and not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"[StateConfig] threshold must be in range [0.0, 1.0], got {self.threshold}")

    def to_dict(self) -> dict[str, object]:
        """ Сериализует конфигурацию в словарь. """
        return {
            'cls_id': self.cls_id,
            'name': self.name,
            'full_name': self.full_name,
            'fiction': self.fiction,
            'alias_of': self.alias_of,
            'stable_min_lim': self.stable_min_lim,
            'resettable': self.resettable,
            'reset_trigger': self.reset_trigger,
            'break_trigger': self.break_trigger,
            'threshold': self.threshold,
        }

    def __str__(self) -> str:
        """ Краткое строковое представление состояния. """
        return f"<StateConfig {self.name} (id={self.cls_id})>"


StateConfigId: TypeAlias = int
StateConfigOrIdType: TypeAlias = Union[StateConfig, StateConfigId]
StateConfigDict: TypeAlias = dict[StateConfigId, StateConfig]
StateConfigTuple: TypeAlias = tuple[StateConfig, ...]
StateConfigTupleTuple: TypeAlias = tuple[StateConfigTuple, ...]
