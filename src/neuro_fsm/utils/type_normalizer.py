from __future__ import annotations

__all__ = ["TypeNormalizer", "CaseMode", "HasName"]

from typing import Any, tuple, Union, Literal, runtime_checkable, Protocol, final
from enum import Enum


CaseMode = Literal["lower", "upper", "keep"]


@runtime_checkable
class HasName(Protocol):
    """ Протокол для объектов, у которых есть атрибут `name: str`. """
    name: str


@final
class TypeNormalizer:
    """
        Утилитный класс для нормализации строк, значений Enum,
        ключей словарей и объектов с атрибутом `.name`.
    """

    __slots__ = ()

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def normalize_dict_keys(input_dict: dict[str, Any], case: CaseMode = "upper") -> dict[str, Any]:
        """
            Преобразует ключи словаря в указанный регистр.
            Вложенные словари не затрагиваются.
            Args:
                input_dict: Исходный словарь.
                case: Режим преобразования регистра — "lower", "upper" или "keep".
            Returns:
                Новый словарь с нормализованными ключами.
        """
        if case == "keep":
            return dict(input_dict)
        return {TypeNormalizer._apply_case(str(k), case): v for k, v in input_dict.items()}

    @staticmethod
    def normalize_enum_str(value: Union[str, Enum], case: CaseMode = "upper") -> str:
        """
            Преобразует Enum или строку в строку с учётом регистра.
            Правила:
                - Если Enum и его .value — строка → берётся .value
                - Если Enum и его .value не строка → берётся .name
                - Если str → используется напрямую
            Args:
                value: Enum или строка для нормализации.
                case: Режим преобразования регистра — "lower", "upper" или "keep".
            Returns:
                Нормализованная строка.
        """
        if isinstance(value, Enum):
            base = value.value if isinstance(value.value, str) else value.name
        else:
            base = str(value)
        return TypeNormalizer._apply_case(base, case)

    @staticmethod
    def normalize_to_tuple(value: Any, case: CaseMode = "keep", *, deep: bool = False) -> tuple[Any, ...]:
        """
            Преобразует значение в кортеж.
            Правила:
                - None → ()
                - tuple → возвращается как есть (или нормализуется, если deep=True)
                - list → преобразуется в tuple (с опцией нормализации строк, если deep=True)
                - str → (строка,) с учётом регистра
                - другие значения → (value,)
            Args:
                value: Исходное значение.
                case: Режим преобразования регистра — "lower", "upper" или "keep".
                deep: Если True, применять преобразование ко всем строкам в списках/кортежах.
            Returns:
                Кортеж с нормализованными значениями.
        """
        if value is None:
            return tuple()

        if isinstance(value, tuple):
            if not deep or case == "keep":
                return value
            return tuple(
                TypeNormalizer._apply_case(x, case) if isinstance(x, str) else x
                for x in value
            )

        if isinstance(value, list):
            if deep and case != "keep":
                return tuple(
                    TypeNormalizer._apply_case(x, case) if isinstance(x, str) else x
                    for x in value
                )
            return tuple(value)

        if isinstance(value, str):
            return (TypeNormalizer._apply_case(value, case),)
        return (value, )

    @staticmethod
    def normalize_to_str_name(value: Union[str, Enum, HasName], *, case: CaseMode = "keep") -> str:
        """
            Преобразует объект, похожий на имя, в строку.
            Правила:
                - str → используется как есть
                - Enum → если .value — строка, берётся .value, иначе .name
                - HasName (например dataclass с атрибутом name) → берётся .name
            Args:
                value: str | Enum | объект с `name: str`.
                case:  Режим преобразования регистра — "lower", "upper" или "keep".
                       Применяется и к значению `.name`.
            Returns:
                Нормализованное имя (строка).
            Raises:
                TypeError: если тип не поддерживается.
        """
        if isinstance(value, str):
            base = value
        elif isinstance(value, Enum):
            base = value.value if isinstance(value.value, str) else value.name
        elif isinstance(value, HasName):
            base = value.name
        else:
            raise TypeError(
                f"normalize_to_str_name: неподдерживаемый тип {type(value)!r}; "
                "ожидался str, Enum или объект с `name: str`."
            )

        return TypeNormalizer._apply_case(base, case)

    @staticmethod
    def _apply_case(s: str, mode: CaseMode) -> str:
        """
            Применяет преобразование регистра к строке.
            Args:
                s: Исходная строка.
                mode: "lower" | "upper" | "keep".
            Returns:
                Строка с применённым преобразованием регистра.
        """
        if mode == "lower":
            return s.lower()
        if mode == "upper":
            return s.upper()
        return s  # keep
