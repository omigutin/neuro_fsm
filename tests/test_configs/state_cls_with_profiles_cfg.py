from src.neuro_fsm.configs import StateConfig
from neuro_fsm.models import ProfileSwitcherStrategies, ProfileNames

class StateClsWithProfilesConfig:
    ENABLE = True

    STATES = (
        StateConfig(cls_id=0, name='EMPTY', stable_min_lim=25, resettable=True, reset_trigger=True, break_trigger=False),
        StateConfig(cls_id=1, name='FULL', stable_min_lim=50, resettable=False, reset_trigger=True, break_trigger=False),
        StateConfig(cls_id=2, name='NO_LIBRA', stable_min_lim=10, resettable=True, reset_trigger=True, break_trigger=True),
        StateConfig(cls_id=3, name='UNKNOWN', stable_min_lim=-1, resettable=True, reset_trigger=False, break_trigger=False),
    )

    STATE_PROFILES = [
        {
            'name': "group1",
            'expected_sequences': (('EMPTY', 'FULL', 'EMPTY'), ),
            'states': {
                'EMPTY': {'stable_min_lim': 5},
                'FULL': {'stable_min_lim': 10},
            },
            'init_states': 0,
            'default_states': 'UNKNOWN',
        },
        {
            'name': "group2",
            'expected_sequences': (('EMPTY', 'FULL', 'EMPTY'), ),
            'states': {
                'EMPTY': {'stable_min_lim': 3},
                'FULL': {'stable_min_lim': 6},
            },
            'init_states': ['EMPTY', ],
            'default_states': ['UNKNOWN', ],
        },
        {
            'name': ProfileNames.DEFAULT,
            'expected_sequences': (('EMPTY', 'FULL', 'EMPTY'), ),
            'states': {
                'EMPTY': {'stable_min_lim': 4, 'resettable': False},
                'FULL': {'stable_min_lim': 8},
            },
            'init_states': 0,
            'default_states': 'UNKNOWN',
        },
    ]

    PROFILE_SWITCHER_STRATEGY = ProfileSwitcherStrategies.BY_MAPPED_ID
    DEFAULT_PROFILE = ProfileNames.DEFAULT
    PROFILE_IDS_MAP = {
        "group1": [101, 102, 103],
        "group2": [201, 202],
        ProfileNames.DEFAULT: []
    }

    RAW_HISTORY_WRITER = {
        "enable": True,
        "format": "txt",
        "path": "{timestamp}_raw.txt",
        "max_age_days": 14,
        "async_mode": False
    }
    STABLE_HISTORY_WRITER = {
        "enable": True,
        "format": "json",
        "path": "{timestamp}_stable.json",
        "fields": ["timestamp", "active_profile", "state", "resetter", "breaker", "stable", "stage_done"],
        "max_age_days": 14,
        "async_mode": False
    }

TEST_SEQUENCES_FOR_DEFAULT = [
    ([0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0], "DEFAULT"),  # чистая последовательность
    ([0, 0, 3, 0, 0, 1, 1, 3, 3, 3, 1, 1, 1, 1, 1, 3, 1, 0, 3, 0, 0, 0], "DEFAULT"),  # встречаются UNKNOWN
    ([0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0], "DEFAULT"),  # EMPTY не подряд, шум в виде FULL
]

TEST_SEQUENCES_FOR_GROUP1 = [
    ([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], "group1"),  # чистая последовательность
    ([0, 0, 0, 0, 0, 3, 1, 1, 1, 3, 1, 1, 1, 1, 3, 1, 1, 1, 0, 0, 3, 3, 0, 0, 0], "group1"),  # встречаются UNKNOWN
]

TEST_SEQUENCES_FOR_GROUP2 = [
    ([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], "group2"),  # чистая последовательность
    ([0, 0, 0, 0, 0, 3, 1, 1, 1, 3, 1, 1, 1, 1, 3, 1, 1, 1, 0, 0, 3, 3, 0, 0, 0], "group2"),  # встречаются UNKNOWN
]
