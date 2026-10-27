__all__ = ['StateFactory']

from ...configs.state_config import StateConfig
from ...configs.profile_config import ProfileConfig
from .state import State
from .types import StateDict


class StateFactory:
    """ Создаёт рабочие состояния (State) профиля из его конфигурации. """

    @staticmethod
    def build(profile_config: ProfileConfig) -> StateDict:
        """ Возвращает словарь cls_id → State для профиля. """
        return {cls_id: StateFactory.create_state(cfg) for cls_id, cfg in profile_config.states.items()}

    @staticmethod
    def create_state(cfg: StateConfig) -> State:
        """ Создаёт State из StateConfig, подставляя значения по умолчанию для незаданных полей. """
        stable_min_lim = cfg.stable_min_lim if cfg.stable_min_lim is not None and cfg.stable_min_lim > 0 else None
        return State(
            cls_id=cfg.cls_id,
            name=cfg.name,
            full_name=cfg.full_name or "",
            is_fiction=bool(cfg.fiction),
            alias_of=cfg.alias_of,
            stable_min_lim=stable_min_lim,
            is_resettable=cfg.resettable if cfg.resettable is not None else True,
            is_resetter=bool(cfg.reset_trigger),
            is_breaker=bool(cfg.break_trigger),
            threshold=float(cfg.threshold) if cfg.threshold is not None else None,
        )
