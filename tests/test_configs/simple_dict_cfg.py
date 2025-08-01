from neuro_fsm.configs import StateConfig
from tests.test_configs.classes import NeuroClasses


class StateMachineConfig:
    STATES = (
        StateConfig(name='NONE', cls_id=-1, stable_min_lim=-1, resettable=True, reset_trigger=False, break_trigger=True),
        StateConfig(name='EMPTY', cls_id=0, stable_min_lim=5, resettable=False, reset_trigger=False, break_trigger=False),
        StateConfig(name='FULL', cls_id=1, stable_min_lim=55, resettable=False, reset_trigger=True, break_trigger=False),
        StateConfig(name='UNKNOWN', cls_id=2, stable_min_lim=-1, resettable=True, reset_trigger=False, break_trigger=False)
    )

    # Ожидаемые последовательности статусов
    EXPECTED_SEQUENCES = ((0, 1, 0), (0, 1, 2, 0), (0, 2, 1, 0), (0, 1, 2, 1, 0), (0, 2, 1, 2),
                          (0, 2, 0, 1, 0), (0, 2, 0, 1, 2, 0))

    # Для видео, которые запускаются с момента, когда стол полон
    INIT_SATES = NeuroClasses.EMPTY
    # Состояние по-умолчанию, если класс состояния не удалось определить
    DEFAULT_STATES = NeuroClasses.UNKNOWN
