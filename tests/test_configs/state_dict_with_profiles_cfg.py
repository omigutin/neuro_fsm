from src.neuro_fsm.core.profiles import ProfileSwitcherStrategies, ProfileNames
from tests.test_configs.classes import NeuroClasses


class StateDictWithProfilesConfig:
    ENABLE = True

    STATES = (
        {'name': NeuroClasses.UNDEFINED.name, 'cls_id': 0, 'full_name': NeuroClasses.UNDEFINED.full_name, 'threshold': 0.5},
        {'name': NeuroClasses.EMPTY.name, 'cls_id': 1, 'full_name': NeuroClasses.EMPTY.full_name},
        {'name': NeuroClasses.FULL.name, 'cls_id': 2, 'full_name': NeuroClasses.FULL.full_name},
        {'name': NeuroClasses.UNKNOWN.name, 'cls_id': 3, 'full_name': NeuroClasses.UNKNOWN.full_name, 'threshold': 0.8},
    )

    STATE_PROFILES = (
        {
            'name': ProfileNames.EMPTY_THEN_FILL,
            'expected_sequences': (
                (NeuroClasses.EMPTY.name, NeuroClasses.FULL.name, NeuroClasses.EMPTY.name),
                (NeuroClasses.EMPTY.name, NeuroClasses.FULL.name, NeuroClasses.EMPTY.name),
            ),
            'states': {
                NeuroClasses.EMPTY.name: {'stable_min_lim': 15, 'resettable': True, 'reset_trigger': True},
                NeuroClasses.FULL.name: {'stable_min_lim': 50, 'resettable': False, 'break_trigger': False},
                NeuroClasses.UNKNOWN.name: {'reset_trigger': True, 'break_trigger': True, 'threshold': 0.3},
            },
            'init_states': (NeuroClasses.EMPTY.name, ),
            'default_states': (NeuroClasses.UNKNOWN.name, ),
        },
        {
            'name': "FULL_FIRST",
            'expected_sequences': (
                (NeuroClasses.EMPTY.name, NeuroClasses.UNKNOWN.name, NeuroClasses.FULL.name, NeuroClasses.EMPTY.name),
                (NeuroClasses.EMPTY.name, NeuroClasses.UNKNOWN.name, NeuroClasses.FULL.name, NeuroClasses.EMPTY.name),
            ),
            'states': {
                NeuroClasses.UNDEFINED.name: {'stable_min_lim': None, 'resettable': True, 'reset_trigger': True},
                NeuroClasses.EMPTY.name: {'stable_min_lim': 5, 'break_trigger': False},
                NeuroClasses.FULL.name: {'stable_min_lim': 10, 'reset_trigger': True},
                NeuroClasses.UNKNOWN.name: {'stable_min_lim': 2},
            },
            'init_states': (NeuroClasses.EMPTY.name,),
            'default_states': (NeuroClasses.UNKNOWN.name,),
        },
    )

    PROFILE_SWITCHER_STRATEGY = ProfileSwitcherStrategies.MIXED

    DEFAULT_PROFILE = ProfileNames.DEFAULT
