from __future__ import annotations

__all__ = ['StateMeta']

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StateMeta:
    """
        Метаданные состояния: описательная часть, определяющая уникальность и отображение состояния.
        Args:
            cls_id (int): Числовой ID, используемый для связи с моделью.
            name (str): Уникальное строковое имя состояния (обычно Enum.name).
            full_name (str): Полное человекочитаемое описание (отображается в UI и логах).
            fiction (bool): Является ли состояние фиктивным (вспомогательным, не возвращаемым моделью напрямую).
    """

    cls_id: int
    name: str
    full_name: str = ""
    fiction: bool = False

    def to_dict(self) -> dict[str, str | int | bool]:
        """
            Сериализует объект в словарь.
            Returns:
                dict: Структура, пригодная для JSON/YAML/отладки.
        """
        return {
            "name": self.name,
            "cls_id": self.cls_id,
            "full_name": self.full_name,
            "fiction": self.fiction
        }

    def describe(self) -> str:
        """
            Возвращает краткое описание состояния в читаемом виде.
            Returns:
                str: Строка вида "STATE_NAME (id=0) — Описание"
        """
        return f"{self.name} (id={self.cls_id}) — {self.full_name or 'Без описания'}"

    def __str__(self) -> str:
        """ Краткая строка для логов и интерфейсов. """
        return f"<StateMeta {self.name} (id={self.cls_id})>"

    def __repr__(self) -> str:
        """ Полное представление для отладки. """
        return (
            f"StateMeta(name={self.name!r}, cls_id={self.cls_id}, "
            f"full_name={self.full_name!r}, fiction={self.fiction})"
        )

    def __post_init__(self):
        """
            Валидация входных данных:
            - name не должен быть пустым;
            - cls_id должен быть неотрицательным.
        """
        if self.cls_id < 0:
            raise ValueError(f"[StateMeta] cls_id must be non-negative, got {self.cls_id}")
        if not self.name:
            raise ValueError("[StateMeta] name must not be empty")
