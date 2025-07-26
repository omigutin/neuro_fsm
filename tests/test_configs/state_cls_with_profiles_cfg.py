from src.neuro_fsm.core.profiles import ProfileNames
from src.neuro_fsm.models import State


class StateClsWithProfilesConfig:
    ENABLE = True

    STATES = (
        State.set(name='UNDEFINED', cls_id=0),
        State.set(name='EMPTY', cls_id=1, threshold=1),
        State.set(name='FULL', cls_id=2, stable_min_lim=6, resettable=False),
        State.set(name='UNKNOWN', cls_id=3, stable_min_lim=None, full_name="UNKNOWN description")
    )

    STATE_PROFILES = [
        {
            'name': ProfileNames.DEFAULT,
            'expected_sequences': ((1, 2, 3, 1), ('EMPTY', 'FULL', 'EMPTY')),
            'states': {},
            'init_states': 1,
            'default_states': 'UNKNOWN',
        },
        {
            'name': "FULL_FIRST",
            'expected_sequences': (('EMPTY', 'UNKNOWN', 'UNDEFINED', 'FULL', 'EMPTY'), (1, 3, 0, 2, 1, 3)),
            'states': {
                'UNDEFINED': {'full_name': "NONE", 'stable_min_lim': None, 'resettable': True, 'reset_trigger': True},
                'EMPTY': {'stable_min_lim': 5, 'break_trigger': False, 'threshold': None},
                'FULL': {'stable_min_lim': 10, 'reset_trigger': True},
                'UNKNOWN': {'stable_min_lim': 2},
            },
            'init_states': ['EMPTY', ],
            'default_states': ['UNKNOWN', ],
        },
    ]

    PROFILE_SWITCHER_STRATEGY = None
    DEFAULT_PROFILE = None
