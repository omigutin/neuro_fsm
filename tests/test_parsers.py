""" Совместимые форматы конфигурации: dict / класс / модуль. """
import types
from dataclasses import dataclass
from enum import Enum

import pytest

from neuro_fsm import FsmManager, ProfileSwitcherStrategies
from tests.helpers import count_done, run
from tests.test_configs.simple_dict_cfg import StateMachineConfig
from tests.test_configs.state_dict_with_profiles_cfg import StateDictWithProfilesConfig
from tests.test_configs.state_other_cls_with_profiles_cfg import StateOtherClsWithProfilesConfig


def test_simple_format_with_singular_init_and_default():
    config = FsmManager.parse_config(StateMachineConfig)
    assert config.enable
    assert config.def_profile == "single"
    profile = config.get_profile("single")
    assert [s.name for s in profile.init_states] == ["EMPTY"]
    assert [s.name for s in profile.default_states] == ["UNKNOWN"]
    assert len(profile.expected_sequences) == 7
    # Отрицательный stable_min_lim трактуется как «никогда не стабильно»
    assert profile.states[-1].stable_min_lim == -1


def test_dict_profiles_format():
    config = FsmManager.parse_config(StateDictWithProfilesConfig)
    assert config.switcher_strategy == ProfileSwitcherStrategies.MIXED
    assert config.def_profile == "empty_then_fill"
    full_first = config.get_profile("full_first")
    assert full_first.states[1].stable_min_lim == 5
    assert full_first.states[0].full_name == ""
    assert config.get_profile("empty_then_fill").states[3].threshold == 0.3
    # Базовое значение без переопределения
    assert full_first.states[3].threshold == 0.8


def test_enum_references_are_resolved_by_name():
    config = FsmManager.parse_config(StateOtherClsWithProfilesConfig)
    profile = config.get_profile("empty_then_fill")
    assert profile.states[0].threshold == 0.4
    assert [s.name for s in profile.expected_sequences[0]] == ["EMPTY", "FULL", "EMPTY"]
    assert config.get_profile("full_first").states[-1].full_name == "NONE"


def test_pc_develop_style_config_runs():
    """ Формат pc_develop: объекты состояний с атрибутами, ссылки Enum с другими cls_id, INIT_STATE как id. """

    @dataclass
    class NNetClass:
        cls_id: int
        name: str

    class NNetClasses(Enum):
        EMPTY = NNetClass(cls_id=100, name="EMPTY")
        FULL = NNetClass(cls_id=101, name="FULL")

    @dataclass
    class State(NNetClass):
        stable_min_lim: int = -1
        resettable: bool = False
        reset_trigger: bool = False
        break_trigger: bool = False
        threshold: float | None = None

    class Config:
        ENABLE = True
        STATES = (
            State(cls_id=0, name="EMPTY", stable_min_lim=2, resettable=True),
            State(cls_id=1, name="FULL", stable_min_lim=2, reset_trigger=True),
            State(cls_id=3, name="UNKNOWN"),
        )
        EXPECTED_SEQUENCES = ((NNetClasses.EMPTY, NNetClasses.FULL, NNetClasses.EMPTY),)
        INIT_STATE = 0
        DEFAULT_STATE = 3
        ADD_CUR_STATE_AFTER_HISTORY_CLEAR = False

    manager = FsmManager(Config)
    assert manager.config.meta == {"add_cur_state_after_history_clear": False}
    fsm = manager.create_fsm()
    assert count_done(run(fsm, [0, 0, 1, 1, 0, 0])) == 1


def test_dict_with_lowercase_keys_and_writers():
    config = FsmManager.parse_config({
        "enable": "true",
        "states": [{"cls_id": 0, "name": "EMPTY", "stable_min_lim": 1}],
        "init_states": "EMPTY",
        "expected_sequences": [],
        "stable_history_writer": {"enable": True, "name": "{timestamp}_stable.yaml"},
        "camera": "cam1",
    })
    assert config.stable_history_writer.enable
    assert not config.raw_history_writer.enable
    assert config.meta == {"camera": "cam1"}


def test_module_config():
    module = types.ModuleType("fsm_cfg")
    module.STATES = [{"cls_id": 0, "name": "EMPTY"}]
    module.INIT_STATE = 0
    assert FsmManager.parse_config(module).get_profile("single") is not None


def test_disabled_config_is_not_parsed_further():
    class Config:
        ENABLE = False
        EXPECTED_SEQUENCES = ()
        INIT_STATE = None

    manager = FsmManager(Config)
    assert not manager.enable
    fsm = manager.create_fsm()
    assert not fsm.enable
    assert fsm.process_state(0).state is None


def test_profile_ids_map_and_default_profile_detection():
    config = FsmManager.parse_config({
        "STATES": [{"cls_id": 0, "name": "EMPTY", "stable_min_lim": 1}],
        "STATE_PROFILES": [
            {"name": "group1", "init_states": 0},
            {"name": "base", "init_state": "EMPTY"},
        ],
        "PROFILE_SWITCHER_STRATEGY": "by_mapped_id",
        "PROFILE_IDS_MAP": {"group1": [1, 2], "base": None},
    })
    assert config.def_profile == "base"
    assert config.profile_ids_map == {"group1": (1, 2), "base": ()}


@pytest.mark.parametrize("raw, error", [
    ({"FOO": 1}, ValueError),
    ({"STATES": [{"cls_id": 0, "name": "EMPTY", "bad_field": 1}], "INIT_STATE": 0}, ValueError),
    ({"STATES": [{"cls_id": 0, "name": "EMPTY"}, {"cls_id": 0, "name": "FULL"}], "INIT_STATE": 0}, ValueError),
    ({"STATES": [{"cls_id": 0, "name": "EMPTY"}], "INIT_STATE": "MISSING"}, ValueError),
    ({"STATES": [{"cls_id": 0, "name": "EMPTY"}], "INIT_STATE": 0, "INIT_STATES": [0]}, ValueError),
    ({"STATES": [{"cls_id": 0, "name": "EMPTY"}], "STATE_PROFILES": [{"name": "p", "init_states": 0,
                                                                       "states": {"EMPTY": {"oops": 1}}}]},
     ValueError),
    ({"STATES": [{"cls_id": 0, "name": "EMPTY"}], "STATE_PROFILES": [{"name": "p", "unknown": 1}]}, ValueError),
    ({"STATES": "EMPTY", "INIT_STATE": 0}, TypeError),
    (42, TypeError),
])
def test_invalid_configs_raise(raw, error):
    with pytest.raises(error):
        FsmManager.parse_config(raw)
