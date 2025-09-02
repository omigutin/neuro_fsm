from src.neuro_fsm.configs import StateConfig
from neuro_fsm.models import ProfileSwitcherStrategies, ProfileNames

class StateClsWithProfilesConfig:
    ENABLE = True

    builder = FsmConfigBuilder()
    builder.set_enable(True)
    builder.set_states_mode("equal")

    profile = builder.add_profile(name="default",
                                  default=True)  # Или можно было бы  потом сделать это через set_default_profile
    profile.add_state(cls_id=0, name='EMPTY', stable_min_lim=25, resettable=True, reset_trigger=True,
                      break_trigger=False)
    profile.add_state(cls_id=1, name='FULL', stable_min_lim=50, resettable=False, reset_trigger=True,
                      break_trigger=False)
    profile.add_state(cls_id=2, name='NO_LIBRA', stable_min_lim=10, resettable=True, reset_trigger=True,
                      break_trigger=True)
    profile.add_state(cls_id=3, name='UNKNOWN', stable_min_lim=None, resettable=True, reset_trigger=False,
                      break_trigger=False)
    profile.set_init_states((2, 0))
    profile.set_def_states(3)
    # Можно задавать по очереди с помощью add_expected_sequences(). set_expected_sequence - принимает либо одну последовательность, либо последовательность последовательностей
    profile.set_expected_sequences(('EMPTY', 'FULL', 'EMPTY'))

    profile = builder.add_profile(name="group1")
    profile.override_state(name_or_id='EMPTY', stable_min_lim=5, resettable=False)
    profile.override_state(name_or_id=1, stable_min_lim=10, break_trigger=True)
    profile.override_init_states('EMPTY')

    profile = builder.add_profile(name="group2")
    profile.override_state(name_or_id='EMPTY', stable_min_lim=15, resettable=False)
    profile.override_def_states(['NO_LIBRA', 'EMPTY'])

    # В данном случае, т.к. builder.add_state не использовалось, то создаём список состояний из default профиля. И уже от него перегружаем нужные атрибуты для других профилей
    builder.build()

    builder = FsmConfigBuilder()
    builder.set_enable(True)
    # В таком случае состояния добавляются как базовые и создаётся автоматом профиль по-умолчанию, в который идёт теже самые состояния.
    builder.add_state(cls_id=0, name='EMPTY', stable_min_lim=25, resettable=True, reset_trigger=True,
                      break_trigger=False)
    builder.add_state(cls_id=1, name='FULL', stable_min_lim=50, resettable=False, reset_trigger=True,
                      break_trigger=False)
    builder.add_state(cls_id=2, name='NO_LIBRA', stable_min_lim=10, resettable=True, reset_trigger=True,
                      break_trigger=True)
    builder.add_state(cls_id=3, name='UNKNOWN', stable_min_lim=None, resettable=True, reset_trigger=False,
                      break_trigger=False)
    builder.set_init_states((2, 0))
    builder.set_def_states(3)
    profile.set_expected_sequence('EMPTY', 'FULL', 'EMPTY')
    profile.override_def_states(['NO_LIBRA', 'EMPTY'])

    builder.build()




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
        "name": "{timestamp}_raw.txt",
        "max_age_days": 14,
        "async_mode": False
    }
    STABLE_HISTORY_WRITER = {
        "enable": True,
        "name": "{timestamp}_stable.yaml",
        "fields": ["timestamp", "active_profile", "state", "resetter", "breaker", "stable", "stage_done"],
        "max_age_days": 14,
        "async_mode": False
    }

TEST_SEQUENCES_FOR_DEFAULT = [
    ([0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0], "default"),  # чистая последовательность
    ([0, 0, 3, 0, 0, 1, 1, 3, 3, 3, 1, 1, 1, 1, 1, 3, 1, 0, 3, 0, 0, 0], "default"),  # встречаются UNKNOWN
    ([0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0], "default"),  # EMPTY не подряд, шум в виде FULL
]

TEST_SEQUENCES_FOR_GROUP1 = [
    ([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], "group1"),  # чистая последовательность
    ([0, 0, 0, 0, 0, 3, 1, 1, 1, 3, 1, 1, 1, 1, 3, 1, 1, 1, 0, 0, 3, 3, 0, 0, 0], "group1"),  # встречаются UNKNOWN
]

TEST_SEQUENCES_FOR_GROUP2 = [
    ([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], "group2"),  # чистая последовательность
    ([0, 0, 0, 0, 0, 3, 1, 1, 1, 3, 1, 1, 1, 1, 3, 1, 1, 1, 0, 0, 3, 3, 0, 0, 0], "group2"),  # встречаются UNKNOWN
]
