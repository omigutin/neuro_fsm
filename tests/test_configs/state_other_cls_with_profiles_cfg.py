from tests.test_configs.classes import NeuroClasses


class StateOtherClsWithProfilesConfig:
    from neuro_fsm.models import ProfileSwitcherStrategies

    ENABLE = True
    PROFILE_SWITCHER_STRATEGY = ProfileSwitcherStrategies.BY_MATCH
    STATES = [NeuroClasses.UNDEFINED, NeuroClasses.EMPTY, NeuroClasses.FULL, NeuroClasses.UNKNOWN.name]

    STATE_PROFILES = (
        {
            'name': "EMPTY_THEN_FILL",
            'expected_sequences': [
                [NeuroClasses.EMPTY, NeuroClasses.FULL, NeuroClasses.EMPTY],
                [NeuroClasses.EMPTY, NeuroClasses.FULL, NeuroClasses.EMPTY],
            ],
            'states': {
                NeuroClasses.EMPTY: {'stable_min_lim': 15, 'resettable': True, 'reset_trigger': True, 'threshold': 0.4},
                NeuroClasses.FULL: {'stable_min_lim': 50, 'resettable': False, 'break_trigger': False},
                NeuroClasses.UNKNOWN: {'reset_trigger': True, 'break_trigger': True},
            },
            'init_states': NeuroClasses.EMPTY,
            'default_states': NeuroClasses.UNKNOWN,
        },
        {
            'name': "FULL_FIRST",
            'expected_sequences': (
                (NeuroClasses.EMPTY, NeuroClasses.UNKNOWN, NeuroClasses.FULL, NeuroClasses.EMPTY),
                (NeuroClasses.EMPTY, NeuroClasses.UNKNOWN, NeuroClasses.FULL, NeuroClasses.EMPTY),
            ),
            'states': {
                NeuroClasses.UNDEFINED: {'full_name': "NONE", 'stable_min_lim': None, 'resettable': True, 'reset_trigger': True},
                NeuroClasses.EMPTY: {'stable_min_lim': 5, 'break_trigger': False, 'threshold': None},
                NeuroClasses.FULL: {'stable_min_lim': 10, 'reset_trigger': True},
                NeuroClasses.UNKNOWN: {'stable_min_lim': 2},
            },
            'init_states': [NeuroClasses.EMPTY, ],
            'default_states': [NeuroClasses.UNKNOWN, ],
        },
    )
