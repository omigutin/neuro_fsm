from __future__ import annotations

__all__ = ["StatesValidator"]

from typing import final

from ..configs import ProfileConfig


@final
class StatesValidator:
    """
        Валидации, связанные с состояниями внутри профилей.

        Политика:
          - Один и тот же `cls_id` может иметь разные `StateConfig` в разных профилях.
          - НИКАКИХ кросс-профильных сравнений не выполняется.
          - Проверяется только внутренняя согласованность каждого профиля по отдельности.

        Что проверяем (выполняемые проверки):
          1) Согласованность ключей и `cls_id` (`_validate_cls_id_consistency`)
             - Если у `StateConfig` есть атрибут `cls_id`, он должен совпадать с ключом в `profile.states`.
             - Цель: поймать рассинхрон между ключом словаря и самим объектом состояния.

          2) Наличие обязательных полей (`_validate_required_fields`)
             - Требуется поле `name`: непустая строка.
             - Цель: обеспечить минимально необходимую идентификацию состояния внутри профиля.

          3) Диапазоны числовых значений (`_validate_value_ranges`)
             - Если присутствует `threshold` → число в диапазоне [0.0, 1.0].
             - Если присутствует `stable_min_lim` → неотрицательное целое.
             - Цель: отловить очевидные ошибки конфигурации порогов/лимитов.

          4) Типы служебных полей (`_validate_field_types`)
             - Если присутствуют: `resettable`, `reset_trigger`, `break_trigger` → должны быть `bool`.
             - Если присутствует `alias_of` → `int` или `None`.
             - Цель: обеспечить корректные типы для управляющих флагов/ссылок.

          5) Уникальность имён внутри профиля (`_validate_unique_names_within_profile`)
             - Поле `name` должно быть уникальным в пределах одного профиля (независимо от `cls_id`).
             - Цель: исключить неоднозначность ссылок/логов по имени состояния.

        Примечание:
          - Все проверки, помеченные как «если присутствует», выполняются только при наличии соответствующих атрибутов
            в `StateConfig`. То есть валидатор не навязывает структуру, но контролирует корректность, если поле задано.
    """

    __slots__ = ()

    def __new__(cls, *a, **k):
        raise TypeError(f"{cls.__name__} is a static namespace; do not instantiate")

    @staticmethod
    def validate(profiles: dict[str, ProfileConfig]) -> None:
        """ Запускает все проверки, связанные с состояниями профилей (внутрипрофильные). """
        StatesValidator._validate_cls_id_consistency(profiles)
        StatesValidator._validate_required_fields(profiles)
        StatesValidator._validate_value_ranges(profiles)
        StatesValidator._validate_field_types(profiles)
        StatesValidator._validate_unique_names_within_profile(profiles)  # ← NEW

    # ---------------- базовая согласованность ----------------

    @staticmethod
    def _validate_cls_id_consistency(profiles: dict[str, ProfileConfig]) -> None:
        """
            Проверяет согласованность ключей словаря `states` и поля `cls_id` в объектах StateConfig.
            Правила:
              - Если в StateConfig есть атрибут `cls_id`, он должен совпадать с ключом словаря профиля.
            Raises:
                ValueError: если ключ словаря и `sc.cls_id` не совпадают.
        """
        for pname, prof in profiles.items():
            for key_cls_id, sc in prof.states.items():
                sc_cls_id = getattr(sc, "cls_id", None)
                if sc_cls_id is not None and sc_cls_id != key_cls_id:
                    raise ValueError(
                        f"StateConfig cls_id mismatch in profile '{pname}': "
                        f"key={key_cls_id}, sc.cls_id={sc_cls_id}."
                    )

    # ---------------- обязательные поля ----------------

    @staticmethod
    def _validate_required_fields(profiles: dict[str, ProfileConfig]) -> None:
        """
        Проверяет наличие ключевых полей у StateConfig (если они предусмотрены твоей моделью).

        Сейчас проверяется:
          - `name`: должен существовать и быть непустой строкой.

        Raises:
            ValueError: если обязательные поля отсутствуют или некорректны.
        """
        for pname, prof in profiles.items():
            for cls_id, sc in prof.states.items():
                if not hasattr(sc, "name"):
                    raise ValueError(
                        f"StateConfig missing required field 'name' in profile '{pname}', cls_id={cls_id}."
                    )
                name = getattr(sc, "name")
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(
                        f"StateConfig field 'name' must be a non-empty string "
                        f"(profile='{pname}', cls_id={cls_id})."
                    )

    # ---------------- диапазоны значений ----------------

    @staticmethod
    def _validate_value_ranges(profiles: dict[str, ProfileConfig]) -> None:
        """
            Проверяет допустимые диапазоны числовых полей (только если поля присутствуют).
            Проверки:
              - `threshold` ∈ [0.0, 1.0]
              - `stable_min_lim` ≥ 0 (целое)
        """
        for pname, prof in profiles.items():
            for cls_id, sc in prof.states.items():
                if hasattr(sc, "threshold"):
                    thr = getattr(sc, "threshold")
                    if not isinstance(thr, (int, float)) or not (0.0 <= float(thr) <= 1.0):
                        raise ValueError(
                            f"StateConfig 'threshold' must be within [0.0, 1.0] "
                            f"(profile='{pname}', cls_id={cls_id}, value={thr!r})."
                        )
                if hasattr(sc, "stable_min_lim"):
                    sml = getattr(sc, "stable_min_lim")
                    if not isinstance(sml, int) or sml < 0:
                        raise ValueError(
                            f"StateConfig 'stable_min_lim' must be a non-negative integer "
                            f"(profile='{pname}', cls_id={cls_id}, value={sml!r})."
                        )

    # ---------------- типы полей ----------------

    @staticmethod
    def _validate_field_types(profiles: dict[str, ProfileConfig]) -> None:
        """
            Проверяет типы некоторых булевых/служебных полей (если они присутствуют).
            Проверки:
              - `resettable`  -> bool
              - `reset_trigger` -> bool
              - `break_trigger` -> bool
              - `alias_of` -> int | None  (если есть и не None)
        """
        for pname, prof in profiles.items():
            for cls_id, sc in prof.states.items():
                if hasattr(sc, "resettable"):
                    v = getattr(sc, "resettable")
                    if not isinstance(v, bool):
                        raise ValueError(
                            f"StateConfig 'resettable' must be bool "
                            f"(profile='{pname}', cls_id={cls_id}, value={v!r})."
                        )
                if hasattr(sc, "reset_trigger"):
                    v = getattr(sc, "reset_trigger")
                    if not isinstance(v, bool):
                        raise ValueError(
                            f"StateConfig 'reset_trigger' must be bool "
                            f"(profile='{pname}', cls_id={cls_id}, value={v!r})."
                        )
                if hasattr(sc, "break_trigger"):
                    v = getattr(sc, "break_trigger")
                    if not isinstance(v, bool):
                        raise ValueError(
                            f"StateConfig 'break_trigger' must be bool "
                            f"(profile='{pname}', cls_id={cls_id}, value={v!r})."
                        )
                if hasattr(sc, "alias_of"):
                    v = getattr(sc, "alias_of")
                    if v is not None and not isinstance(v, int):
                        raise ValueError(
                            f"StateConfig 'alias_of' must be int or None "
                            f"(profile='{pname}', cls_id={cls_id}, value={v!r})."
                        )

    # ---------------- уникальность имён внутри профиля ----------------

    @staticmethod
    def _validate_unique_names_within_profile(profiles: dict[str, ProfileConfig]) -> None:
        """
            Запрещает дубли `name` внутри одного профиля (независимо от cls_id).
            Raises:
                ValueError: если обнаружены повторяющиеся имена состояний внутри профиля.
        """
        for pname, prof in profiles.items():
            seen: dict[str, int] = {}
            for cls_id, sc in prof.states.items():
                name = getattr(sc, "name", None)
                if not isinstance(name, str):
                    # Отловится в _validate_required_fields; здесь просто пропустим.
                    continue
                if name in seen:
                    prev_cls_id = seen[name]
                    raise ValueError(
                        f"Duplicate state name '{name}' within profile '{pname}' "
                        f"(cls_id={prev_cls_id} and cls_id={cls_id}). "
                        "State names must be unique within a profile."
                    )
                seen[name] = cls_id
