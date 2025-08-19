__all__ = ['StateConfigParser']

import warnings
from dataclasses import replace
from typing import Any, Sequence, Union, Optional
from enum import Enum

from ..configs.state_config import StateConfig, StateConfigDict


class StateConfigParser:
    """
        Универсальный парсер состояний из конфигураций.
        Поддерживает форматы: JSON/YAML словари, Enum, вложенные структуры профилей.
    """

    @staticmethod
    def build_dict(raw_state_configs: Sequence[Any], *, name_check: bool = True) -> StateConfigDict:
        """
            Массовая загрузка состояний из различных форматов (dict, Enum, StateConfig).
            Args:
                raw_state_configs (Sequence[dict | Enum | StateConfig]): Список элементов для парсинга.
                name_check (bool): Требовать наличие name (True — для базовых, False — для overrides).
            Returns:
                StateConfigDict: Словарь состояний cls_id → StateConfig.
        """
        state_configs: StateConfigDict = {}

        for item in raw_state_configs:
            if isinstance(item, StateConfig):
                config = item
            elif isinstance(item, dict):
                config = StateConfigParser._from_dict(item)
            elif isinstance(item, Enum) or (hasattr(item, "cls_id") and hasattr(item, "name")):
                config = StateConfigParser._from_enum(item)
            else:
                raise TypeError(f"[StateConfigParser] Unsupported state config type: {type(item)}")

            if config.cls_id in state_configs:
                raise ValueError(f"[StateConfigParser] Duplicate cls_id detected: {config.cls_id}")

            if name_check and not config.name:
                raise ValueError(f"[StateConfigParser] Missing required 'name' for cls_id={config.cls_id}")

            state_configs[config.cls_id] = config

        StateConfigParser._validate_aliases(state_configs)
        return state_configs

    @staticmethod
    def build_dict_with_overrides(states_override: dict, base_states: StateConfigDict) -> StateConfigDict:
        """
            Создаёт словарь StateConfig с учётом переопределений:
            - Парсит overrides через build_dict
            - Проверяет наличие таких состояний в базовом словаре
            - Мержит параметры, не заменяя cls_id / name
        """
        overrides_states = {}
        for key, override in states_override.items():
            if isinstance(key, str):
                config = StateConfigParser._from_name(key, base_states, override)
            elif isinstance(key, int):
                config = StateConfigParser._from_id(key, base_states, override)
            else:
                raise TypeError("StateConfig override keys must be str (name) or int (cls_id)")
            overrides_states[config.cls_id] = config

        overrides_states = StateConfigParser._merge_with_base(overrides_states, base_states)
        return overrides_states

    @staticmethod
    def _from_name(name: str, base_state_dict: StateConfigDict, overrides: dict = None) -> StateConfig:
        for cfg in base_state_dict.values():
            if cfg.name == name:
                return replace(cfg, **(overrides or {}))
        raise ValueError(f"StateConfig with name='{name}' not found in base_state_dict")

    @staticmethod
    def _from_id(cls_id: int, base_state_dict: StateConfigDict, overrides: dict = None) -> StateConfig:
        cfg = base_state_dict.get(cls_id)
        if cfg is None:
            raise ValueError(f"StateConfig with cls_id={cls_id} not found in base_state_dict")
        return replace(cfg, **(overrides or {}))

    @staticmethod
    def _validate_aliases(state_configs: StateConfigDict) -> None:
        """
            Проверяет корректность всех alias_of:
            - Ссылается на существующий cls_id
            - Не является вложенным alias → alias
        """
        for config in state_configs.values():
            if config.alias_of is None:
                continue

            base = state_configs.get(config.alias_of)
            if base is None:
                raise ValueError(
                    f"[StateConfigParser] Alias '{config.name}' (cls_id={config.cls_id}) "
                    f"points to unknown cls_id={config.alias_of}"
                )

            if base.alias_of is not None:
                raise ValueError(
                    f"[StateConfigParser] Alias '{config.name}' (cls_id={config.cls_id}) "
                    f"points to another alias (cls_id={base.cls_id}). Nested aliases are not allowed."
                )

    @staticmethod
    def _from_dict(source: dict[str, Any]) -> StateConfig:
        """
            Создание State из словаря верхнего уровня.
            Args:
                source (dict): Словарь с ключами:
                          - 'name', 'cls_id', 'full_name', 'fiction' (для meta)
                          - 'stable_min_lim', 'resettable', 'reset_trigger', 'break_trigger', 'threshold' (для params)
            Returns:
                StateConfig: Объект состояния.
        """
        stable_min_lim = source.get("stable_min_lim", None)
        return StateConfig(
            cls_id=source["cls_id"],
            name=source["name"],
            full_name=source.get("full_name", None),
            fiction=source.get("fiction", None),
            alias_of=source.get("alias_of", None),
            stable_min_lim=None if stable_min_lim and stable_min_lim < 0 else stable_min_lim,
            resettable=source.get("resettable", None),
            reset_trigger=source.get("reset_trigger", None),
            break_trigger=source.get("break_trigger", None),
            threshold=source.get("threshold", None),
        )

    @staticmethod
    def _from_enum(source: Union[Enum, Any]) -> StateConfig:
        """
            Преобразует enum-член (с value: NeuroClass) или объект с атрибутами в State.
            Args:
                source (Enum | Any): элемент перечисления или совместимый объект.
            Returns:
                State: экземпляр состояния.
        """
        obj = source.value if isinstance(source, Enum) else source
        stable_min_lim = getattr(obj, "stable_min_lim", None)
        return StateConfig(
            cls_id=getattr(obj, "cls_id"),
            name=getattr(obj, "name"),
            full_name=getattr(obj, "full_name", None),
            fiction=getattr(obj, "fiction", None),
            alias_of=getattr(obj, "alias_of", None),
            stable_min_lim=None if stable_min_lim and stable_min_lim < 0 else stable_min_lim,
            resettable=getattr(obj, "resettable", None),
            reset_trigger=getattr(obj, "reset_trigger", None),
            break_trigger=getattr(obj, "break_trigger", None),
            threshold=getattr(obj, "threshold", None),
        )

    @staticmethod
    def _merge_with_base(overrides_states: StateConfigDict, base_states: StateConfigDict) -> StateConfigDict:
        """
            Создаёт новый словарь состояний с применёнными override-параметрами.
            При отсутствии параметра в override используется значение из base.
        """
        def _merge_value(override_val: float | None, base_val: float | None, default: Optional[float] = 0.0) -> float | None:
            if override_val not in (None, default):
                return override_val
            if base_val not in (None, default):
                return base_val
            return None

        def _merge_flag(override: bool | None, base: bool | None, default: bool = False) -> bool:
            if override is not None:
                return override
            if base is not None:
                return base
            return default

        result = base_states.copy()

        for cls_id, os in overrides_states.items():
            base_state = result[cls_id]

            if base_state.name != os.name:
                warnings.warn(
                    f"[StateConfigParser] Base state name='{base_state.name}' "
                    f"differs from override state name='{os.name}' for cls_id={cls_id}. Using base state name."
                )

            stable_min_lim = _merge_value(os.stable_min_lim, base_state.stable_min_lim, None)

            result[cls_id] = StateConfig(
                cls_id=base_state.cls_id,
                name=base_state.name,
                full_name=os.full_name or base_state.full_name or "",
                alias_of=os.alias_of or base_state.alias_of,
                fiction=_merge_flag(os.fiction, base_state.fiction, False),
                stable_min_lim=None if stable_min_lim and stable_min_lim < 0 else stable_min_lim,
                resettable=_merge_flag(os.resettable, base_state.resettable, True),
                reset_trigger=_merge_flag(os.reset_trigger, base_state.reset_trigger, False),
                break_trigger=_merge_flag(os.break_trigger, base_state.break_trigger, False),
                threshold=_merge_value(os.threshold, base_state.threshold, 0.0),
            )

        return result
