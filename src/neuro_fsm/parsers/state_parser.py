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
        result: StateConfigDict = {}

        for item in raw_state_configs:
            if isinstance(item, StateConfig):
                config = item
            elif isinstance(item, dict):
                config = StateConfigParser._from_dict(item)
            elif isinstance(item, Enum) or (hasattr(item, "cls_id") and hasattr(item, "name")):
                config = StateConfigParser._from_enum(item)
            else:
                raise TypeError(f"[StateConfigParser] Unsupported state config type: {type(item)}")

            if config.cls_id in result:
                raise ValueError(f"[StateConfigParser] Duplicate cls_id detected: {config.cls_id}")

            result[config.cls_id] = config

        return result

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
        return StateConfigParser._merge_with_base(overrides_states, base_states)

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
            name=source["name"],
            cls_id=source["cls_id"],
            full_name=source.get("full_name", ""),
            fiction=source.get("fiction", False),
            stable_min_lim=source.get("stable_min_lim"),
            resettable=source.get("resettable", False),
            reset_trigger=source.get("reset_trigger", False),
            break_trigger=source.get("break_trigger", False),
            threshold=source.get("threshold"),
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
            name=getattr(obj, "name"),
            cls_id=getattr(obj, "cls_id"),
            full_name=getattr(obj, "full_name", ""),
            fiction=getattr(obj, "fiction", False),
            stable_min_lim=getattr(obj, "stable_min_lim", None),
            resettable=getattr(obj, "resettable", False),
            reset_trigger=getattr(obj, "reset_trigger", False),
            break_trigger=getattr(obj, "break_trigger", False),
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
            if base_state.name != override_state.name:
                warnings.warn(
                    f"[StateConfigParser] Skipping override due to name mismatch for cls_id={cls_id}: "
                    f"override='{override_state.name}', base='{base_state.name}'"
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
        result = base_states.copy()
        for cls_id, os in overrides_states.items():
            original = result[cls_id]
            result[cls_id] = StateConfig(
                cls_id=cls_id,
                name=os.name,
                full_name=os.full_name or original.full_name,
                fiction=os.fiction,
                stable_min_lim=os.stable_min_lim if os.stable_min_lim is not None else original.stable_min_lim,
                resettable=os.resettable,
                reset_trigger=os.reset_trigger,
                break_trigger=os.break_trigger,
                threshold=os.threshold if os.threshold is not None else original.threshold,
            )
        return result
