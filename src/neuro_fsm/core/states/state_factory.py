__all__ = ['StateFactory']

from ...configs import StateConfigDict, StateConfig
from .state_meta import StateMeta
from .state_params import StateParams
from .state import State, StateDict


class StateFactory:
    @staticmethod
    def build(configs: StateConfigDict) -> StateDict:
        """ Создаёт словарь состояний из словаря конфигураций """
        return {k: StateFactory._create_state(v) for k, v in configs.items()}

    @staticmethod
    def _create_state(cfg: StateConfig) -> State:
        """ Создание нового State из StateConfig """
        meta = StateMeta(
            cls_id=cfg.cls_id,
            name=cfg.name,
            full_name=cfg.full_name,
            fiction=cfg.fiction
        )
        params = StateParams(
            stable_min_lim=cfg.stable_min_lim,
            resettable=cfg.resettable,
            reset_trigger=cfg.reset_trigger,
            break_trigger=cfg.break_trigger,
            threshold=cfg.threshold
        )
        return State(meta, params)
