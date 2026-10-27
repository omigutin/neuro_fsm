from __future__ import annotations

__all__ = ["StatesValidator"]

from typing import final

from ..configs import ProfileConfig, StateConfig


@final
class StatesValidator:
    """
        Проверки состояний профилей.
        Внутри профиля:
            - ключ словаря совпадает с cls_id;
            - имена уникальны;
            - типы заданных (не None) полей корректны;
            - alias_of ссылается на существующее состояние, вложенные алиасы запрещены.
        Между профилями (только режим "equal"):
            - одинаковый набор пар (cls_id, name).
        Диапазоны stable_min_lim и threshold проверяются в StateConfig.
    """

    __slots__ = ()

    _BOOL_FIELDS: tuple[str, ...] = ("fiction", "resettable", "reset_trigger", "break_trigger")

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def validate(profiles: dict[str, ProfileConfig], equal_states: bool = False) -> None:
        """ Запускает все проверки состояний. """
        for name, profile in profiles.items():
            StatesValidator._validate_profile(name, profile)
        if equal_states:
            StatesValidator._validate_equal_sets(profiles)

    @staticmethod
    def _validate_profile(pname: str, profile: ProfileConfig) -> None:
        """ Внутрипрофильные проверки. """
        seen_names: dict[str, int] = {}
        for key, sc in profile.states.items():
            if not isinstance(sc, StateConfig):
                raise ValueError(f"Profile '{pname}': state {key!r} must be StateConfig, got {type(sc)!r}.")
            if sc.cls_id != key:
                raise ValueError(f"Profile '{pname}': key {key} differs from state cls_id {sc.cls_id}.")
            if sc.name in seen_names:
                raise ValueError(
                    f"Profile '{pname}': duplicate state name '{sc.name}' "
                    f"(cls_id={seen_names[sc.name]} and cls_id={key})."
                )
            seen_names[sc.name] = key
            StatesValidator._validate_field_types(pname, sc)

        for sc in profile.states.values():
            if sc.alias_of is None:
                continue
            base = profile.states.get(sc.alias_of)
            if base is None:
                raise ValueError(f"Profile '{pname}': {sc} alias_of={sc.alias_of} points to unknown state.")
            if base.alias_of is not None:
                raise ValueError(f"Profile '{pname}': {sc} points to alias {base}. Nested aliases are not allowed.")

    @staticmethod
    def _validate_field_types(pname: str, sc: StateConfig) -> None:
        """ Проверка типов заданных полей. """
        for field_name in StatesValidator._BOOL_FIELDS:
            value = getattr(sc, field_name)
            if value is not None and not isinstance(value, bool):
                raise ValueError(f"Profile '{pname}': {sc} field '{field_name}' must be bool, got {value!r}.")
        checks = (
            ("stable_min_lim", sc.stable_min_lim, int),
            ("alias_of", sc.alias_of, int),
            ("threshold", sc.threshold, (int, float)),
        )
        for field_name, value, expected in checks:
            if value is not None and (isinstance(value, bool) or not isinstance(value, expected)):
                raise ValueError(f"Profile '{pname}': {sc} field '{field_name}' has invalid type: {value!r}.")
        if sc.full_name is not None and not isinstance(sc.full_name, str):
            raise ValueError(f"Profile '{pname}': {sc} field 'full_name' must be str, got {sc.full_name!r}.")

    @staticmethod
    def _validate_equal_sets(profiles: dict[str, ProfileConfig]) -> None:
        """ В режиме "equal" все профили имеют одинаковый набор (cls_id, name). """
        reference_name, reference = next(iter(profiles.items()))
        reference_set = {(s.cls_id, s.name) for s in reference.states.values()}
        for name, profile in profiles.items():
            current = {(s.cls_id, s.name) for s in profile.states.values()}
            if current != reference_set:
                raise ValueError(
                    f"States mode 'equal': profile '{name}' states differ from profile '{reference_name}': "
                    f"{sorted(current ^ reference_set)}."
                )
