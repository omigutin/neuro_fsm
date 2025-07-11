from __future__ import annotations

__all__ = ['State', 'StateOrIdType', 'StatesTuple', 'StatesDict', 'StatesTupleTuple', 'StatesDictTuple']

from dataclasses import dataclass
from typing import TypeAlias, Union, Optional

from .state_meta import StateMeta
from .state_params import StateParams


@dataclass(slots=True)
class State:
    """
        Класс объединяет описание состояния (StateMeta) и поведенческие параметры (StateParams).
        Используется в профилях машины состояний и хранит:
        - идентификатор состояния,
        - имя и отображаемое описание,
        - логику обработки (сбросы, прерывания и т.д.).
    """

    meta: StateMeta
    params: StateParams

    @property
    def name(self) -> str:
        """ Уникальное строковое имя состояния (Enum.name). """
        return self.meta.name

    @property
    def cls_id(self) -> int:
        """ Числовой идентификатор состояния. """
        return self.meta.cls_id

    @property
    def full_name(self) -> str:
        """ Человекочитаемое описание состояния (для интерфейсов и логов). """
        return self.meta.full_name

    @property
    def is_fiction(self) -> bool:
        return self.meta.fiction

    @property
    def is_stability_enabled(self) -> bool:
        return self.params.is_stability_enabled

    @property
    def is_resettable(self) -> bool:
        """ Можно ли сбрасывать это состояние вручную. """
        return self.params.is_resettable

    @property
    def is_resetter(self) -> bool:
        """ Возвращает True, если состояние инициирует сброс других состояний. """
        return self.params.is_resetter

    @property
    def is_breaker(self) -> bool:
        """ Возвращает True, если состояние завершает текущую обработку. """
        return self.params.is_breaker

    @property
    def stable_min_lim(self) -> Optional[int]:
        return self.params.stable_min_lim

    @property
    def threshold(self) -> Optional[float]:
        return self.params.threshold

    @classmethod
    def set(cls,
            cls_id: int,
            name: str,
            full_name: str = "",
            fiction: bool = False,
            stable_min_lim: Optional[int] = None,
            resettable: bool = False,
            reset_trigger: bool = False,
            break_trigger: bool = False,
            threshold: Optional[float] = None
            ) -> State:
        """ Создание нового объекта """
        meta = StateMeta(cls_id, name, full_name, fiction)
        params = StateParams(stable_min_lim, resettable, reset_trigger, break_trigger, threshold)
        return cls(meta, params)

    def to_dict(self) -> dict[str, str | int | dict[str, str | int | float | None]]:
        """
            Сериализует состояние в словарь.
            Returns:
                dict: Словарь с мета-информацией и параметрами.
        """
        return {
            "name": self.name,
            "cls_id": self.cls_id,
            "full_name": self.full_name,
            "fiction": self.is_fiction,
            "params": self.params.to_dict()
        }

    def describe(self) -> str:
        """ Возвращает строку для UI или логов. """
        return f"{self.name} (id={self.cls_id}) — {self.full_name or 'Без описания'}"

    def __eq__(self, other: State) -> bool:
        """
            Проверяет логическую идентичность двух состояний по имени и ID.
            Поведенческие параметры (params) не сравниваются.
            Args:
                other (State): Другое состояние.

            Returns:
                bool: True, если name и cls_id совпадают.
        """
        if not isinstance(other, State):
            return False
        return self.name == other.name and self.cls_id == other.cls_id

    def __str__(self) -> str:
        """ Краткое строковое представление состояния. """
        return f"<State {self.name} (id={self.cls_id})>"

    def __repr__(self) -> str:
        """ Подробное строковое представление для отладки. """
        return f"State(name={self.name!r}, cls_id={self.cls_id}, full_name={self.full_name!r})"


StatesDict: TypeAlias = dict[int, State]
StateOrIdType: TypeAlias = Union[State, int]

StatesTuple: TypeAlias = tuple[State, ...]
StatesTupleTuple: TypeAlias = tuple[StatesTuple, ...]
StatesDictTuple: TypeAlias = dict[StatesTuple, int]
