__all__ = ['StateFactory']

from ...configs import StateConfigDict, StateConfig

from .state import State, StateDict


class StateFactory:
    """ Создаёт словарь состояний из словаря настроек состояний """

    @staticmethod
    def build(state_configs: StateConfigDict) -> StateDict:
        states: StateDict = {}
        for cfg in state_configs.values():
            states[cfg.cls_id] = StateFactory._create_state(cfg)
        StateFactory._validate_aliases(states)
        return states

    @staticmethod
    def _create_state(cfg: StateConfig) -> State:
        return State(
            cls_id=cfg.cls_id,
            name=cfg.name,
            full_name=cfg.full_name or "",
            is_fiction=cfg.fiction if cfg.fiction is not None else False,
            alias_of=cfg.alias_of,
            stable_min_lim=cfg.stable_min_lim if cfg.stable_min_lim is not None else 0,
            is_resettable=cfg.resettable if cfg.resettable is not None else True,
            is_resetter=cfg.reset_trigger if cfg.reset_trigger is not None else False,
            is_breaker=cfg.break_trigger if cfg.break_trigger is not None else False,
            threshold=cfg.threshold if cfg.threshold is not None else 0.0,
        )

    @staticmethod
    def _validate_aliases(states: StateDict) -> None:
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
