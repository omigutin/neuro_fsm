__all__ = ['StateConfigParser']

import warnings
from typing import Any, Sequence, Union
from enum import Enum

from ..configs import StateConfig, StateConfigDict


class StateConfigParser:
    """
        Универсальный парсер состояний из конфигураций.
        Поддерживает форматы: JSON/YAML словари, Enum, вложенные структуры профилей.
    """

    @staticmethod
    def build_dict(raw_state_configs: Sequence[Any]) -> StateConfigDict:
        """
            Массовая загрузка состояний из различных форматов (dict, Enum, StateConfig).
            Args:
                raw_state_configs (Sequence[dict | Enum | StateConfig]): Список элементов для парсинга.
            Returns:
                StateConfigDict: Словарь состояний cls_id → StateConfig.
        """
        def _validate_aliases(state_configs: StateConfigDict) -> None:
            for state in state_configs.values():
                if state.alias_of is not None and state.alias_of not in state_configs:
                    raise ValueError(
                        f"[StateConfigParser] Alias '{state.name}' (cls_id={state.cls_id}) "
                        f"points to unknown cls_id={state.alias_of}"
                    )

        stats_configs: StateConfigDict = {}

        for item in raw_state_configs:
            if isinstance(item, StateConfig):
                state_config = item
            elif isinstance(item, dict):
                state_config = StateConfigParser._from_dict(item)
            elif isinstance(item, Enum) or (hasattr(item, "cls_id") and hasattr(item, "name")):
                state_config = StateConfigParser._from_enum(item)
            else:
                raise TypeError(f"[StateConfigParser] Unsupported state config type: {type(item)}")

            if state_config.cls_id in stats_configs:
                raise ValueError(f"[StateConfigParser] Duplicate cls_id detected: {state_config.cls_id}")

            stats_configs[state_config.cls_id] = state_config

        _validate_aliases(stats_configs)

        return stats_configs

    @staticmethod
    def build_dict_with_overrides(overrides_raw: Sequence[Any], base_states: StateConfigDict) -> StateConfigDict:
        """
            Создаёт словарь StateConfig с учётом переопределений:
            - Парсит overrides через build_dict
            - Проверяет наличие таких состояний в базовом словаре
            - Мержит параметры, не заменяя cls_id / name
        """
        overrides_states = StateConfigParser.build_dict(overrides_raw)
        overrides_states = StateConfigParser._validate_states(overrides_states, base_states)
        overrides_states = StateConfigParser._merge_with_base(overrides_states, base_states)
        return overrides_states

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
        return StateConfig(
            cls_id=source["cls_id"],
            name=source["name"],
            full_name=source.get("full_name", None),
            fiction=source.get("fiction", None),
            alias_of=source.get("alias_of", None),
            stable_min_lim=source.get("stable_min_lim", None),
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
        return StateConfig(
            cls_id=getattr(obj, "cls_id"),
            name=getattr(obj, "name"),
            full_name=getattr(obj, "full_name", None),
            fiction=getattr(obj, "fiction", None),
            alias_of=getattr(obj, "alias_of", None),
            stable_min_lim=getattr(obj, "stable_min_lim", None),
            resettable=getattr(obj, "resettable", None),
            reset_trigger=getattr(obj, "reset_trigger", None),
            break_trigger=getattr(obj, "break_trigger", None),
            threshold=getattr(obj, "threshold", None),
        )

    @staticmethod
    def _validate_states(overrides_states: StateConfigDict, base_states: StateConfigDict) -> StateConfigDict:
        """
            Проверяет состояния из overrides и исключает те, что не найдены в base.
            Если имя отличается — также исключается.
            Возвращает отфильтрованный словарь override-состояний.
        """
        valid_overrides: StateConfigDict = {}

        for cls_id, override_state in overrides_states.items():
            base_state = base_states.get(cls_id)
            if base_state is None:
                warnings.warn(
                    f"[StateConfigParser] Skipping override for unknown state id={cls_id}, name='{override_state.name}'"
                )
                continue
            valid_overrides[cls_id] = override_state

        return valid_overrides

    @staticmethod
    def _merge_with_base(overrides_states: StateConfigDict, base_states: StateConfigDict) -> StateConfigDict:
        """
            Создаёт новый словарь состояний с применёнными override-параметрами.
            При отсутствии параметра в override используется значение из base.
        """
        def _merge_value(override_val: float | None, base_val: float | None, default: float = 0.0) -> float | None:
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

            result[cls_id] = StateConfig(
                cls_id=base_state.cls_id,
                name=base_state.name,
                full_name=os.full_name or base_state.full_name or "",
                alias_of=os.alias_of or base_state.alias_of,
                fiction=_merge_flag(os.fiction, base_state.fiction, False),
                stable_min_lim=_merge_value(os.stable_min_lim, base_state.stable_min_lim, 0.0),
                resettable=_merge_flag(os.resettable, base_state.resettable, True),
                reset_trigger=_merge_flag(os.reset_trigger, base_state.reset_trigger, False),
                break_trigger=_merge_flag(os.break_trigger, base_state.break_trigger, False),
                threshold=_merge_value(os.threshold, base_state.threshold, 0.0),
            )

        return result
