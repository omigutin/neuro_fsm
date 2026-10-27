__all__ = ['StateConfigParser']

from enum import Enum
from typing import Any, Iterable, Mapping

from ..configs.state_config import StateConfig, StateConfigDict


class StateConfigParser:
    """
        Разбор списка состояний из конфигурации.
        Элемент списка может быть:
            - StateConfig;
            - dict с ключами полей StateConfig;
            - Enum, значение которого содержит атрибуты cls_id и name (например, NNetClasses);
            - любой объект с атрибутами cls_id и name (например, State из pc_develop).
    """

    _FIELDS: tuple[str, ...] = ("cls_id", "name", "full_name", "fiction", "alias_of", "stable_min_lim",
                                "resettable", "reset_trigger", "break_trigger", "threshold")

    @staticmethod
    def build_dict(raw_state_configs: Iterable[Any] | Mapping[Any, Any]) -> StateConfigDict:
        """ Возвращает словарь cls_id → StateConfig. Дубли cls_id запрещены. """
        items = raw_state_configs.values() if isinstance(raw_state_configs, Mapping) else raw_state_configs
        state_configs: StateConfigDict = {}
        for item in items:
            config = StateConfigParser.parse_one(item)
            if config.cls_id in state_configs:
                raise ValueError(f"[StateConfigParser] Duplicate cls_id detected: {config.cls_id}")
            state_configs[config.cls_id] = config
        return state_configs

    @staticmethod
    def parse_one(item: Any) -> StateConfig:
        """ Разбирает одно состояние. """
        if isinstance(item, StateConfig):
            return item
        if isinstance(item, Mapping):
            unknown = set(item) - set(StateConfigParser._FIELDS)
            if unknown:
                raise ValueError(f"[StateConfigParser] Unknown state fields {sorted(unknown)} in {item!r}")
            values = dict(item)
        else:
            source = item.value if isinstance(item, Enum) else item
            if not (hasattr(source, "cls_id") and hasattr(source, "name")):
                raise TypeError(f"[StateConfigParser] Unsupported state config: {item!r}")
            values = {f: getattr(source, f) for f in StateConfigParser._FIELDS if hasattr(source, f)}
        if "cls_id" not in values or "name" not in values:
            raise ValueError(f"[StateConfigParser] State must have 'cls_id' and 'name': {item!r}")
        stable_min_lim = values.get("stable_min_lim")
        if stable_min_lim is not None and stable_min_lim < 0:
            values["stable_min_lim"] = None
        return StateConfig(**values)
