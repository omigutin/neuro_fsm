__all__ = ['StateFactory']

from ...configs import StateConfigDict, StateConfig, ProfileConfig
from .state import State, StateDict


class StateFactory:
    """Создаёт словарь состояний из глобальной и профильной конфигурации."""

    @staticmethod
    def build(global_config: StateConfigDict, profile_config: ProfileConfig) -> StateDict:
        """
            Создаёт словарь состояний для профиля с учётом перегрузки параметров.
            Args:
                global_config (StateConfigDict): Глобальные настройки всех состояний.
                profile_config (StateConfigDict): Частичные переопределения.
            Returns:
                StateDict: Словарь cls_id → State
        """
        states: StateDict = {}

        for cls_id in global_config:
            merged_config = StateFactory._merge_configs(global_config[cls_id], profile_config.states.get(cls_id))
            states[cls_id] = StateFactory._create_state(merged_config)

        StateFactory._validate_aliases(states)

        return states

    @staticmethod
    def _merge_configs(base: StateConfig, override: StateConfig) -> StateConfig:
        """ Мержит два конфига: глобальный и профильный. Приоритет у override. """
        return StateConfig(
            cls_id=base.cls_id,
            name=override.name or base.name,
            full_name=override.full_name or base.full_name,
            fiction=override.fiction if override.fiction is not None else base.fiction,
            alias_of=override.alias_of or base.alias_of,
            stable_min_lim=override.stable_min_lim if override.stable_min_lim is not None else base.stable_min_lim,
            resettable=override.resettable if override.resettable is not None else base.resettable,
            reset_trigger=override.reset_trigger if override.reset_trigger is not None else base.reset_trigger,
            break_trigger=override.break_trigger if override.break_trigger is not None else base.break_trigger,
            threshold=override.threshold if override.threshold is not None else base.threshold,
        )

    @staticmethod
    def _create_state(cfg: StateConfig) -> State:
        """ Создаёт объект State из StateConfig. """
        return State(
            cls_id=cfg.cls_id,
            name=cfg.name,
            full_name=cfg.full_name or "",
            is_fiction=cfg.fiction if cfg.fiction is not None else False,
            alias_of=cfg.alias_of,
            stable_min_lim=cfg.stable_min_lim or 0,
            is_resettable=cfg.resettable if cfg.resettable is not None else True,
            is_resetter=cfg.reset_trigger if cfg.reset_trigger is not None else False,
            is_breaker=cfg.break_trigger if cfg.break_trigger is not None else False,
            threshold=cfg.threshold or 0.0,
        )

    @staticmethod
    def _validate_aliases(states: StateDict) -> None:
        """Проверяет, что алиасы валидны и не вложены."""
        for state in states.values():
            if state.alias_of is not None:
                base = states.get(state.alias_of)
                if base is None:
                    raise ValueError(
                        f"[StateFactory] State '{state.name}' (id={state.cls_id}) "
                        f"alias_of={state.alias_of} — base class does not exist"
                    )
                if base.alias_of is not None:
                    raise ValueError(
                        f"[StateFactory] State '{state.name}' (id={state.cls_id}) "
                        f"alias_of={state.alias_of} — alias cannot refer to another alias ({base.name})"
                    )
