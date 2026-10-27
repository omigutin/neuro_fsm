""" Билдер конфигурации и проверки конфигурации. """
import pytest

from neuro_fsm import (FsmConfig, FsmConfigBuilder, ProfileConfig, ProfileConfigBuilder, ProfileNames,
                       ProfileSwitcherStrategies, StateConfig)
from tests.helpers import base_builder
from tests.test_configs.state_cls_with_profiles_cfg import make_builder


def seq_names(profile: ProfileConfig) -> list[list[str]]:
    return [[s.name for s in seq] for seq in profile.expected_sequences]


def test_equal_mode_inheritance():
    config = make_builder().build()
    assert isinstance(config, FsmConfig)
    assert config.def_profile == "default"
    assert [p.name for p in config.profile_configs] == ["default", "group1", "group2"]

    default, group1, group2 = (config.get_profile(n) for n in ("default", "group1", "group2"))
    assert group1.states[0].stable_min_lim == 5 and group1.states[0].resettable is False
    assert group1.states[1].stable_min_lim == 10 and group1.states[1].break_trigger is True
    # Остальные параметры унаследованы
    assert group1.states[1].reset_trigger is True
    assert group1.states[2] == default.states[2]
    # init — свой, default/sequences — унаследованы
    assert [s.name for s in group1.init_states] == ["EMPTY"]
    assert [s.name for s in group1.default_states] == ["UNKNOWN"]
    assert seq_names(group1) == [["EMPTY", "FULL", "EMPTY"]]
    # Ссылки в init/sequences указывают на изменённые состояния профиля
    assert group2.init_states[-1] is group2.states[0]
    assert group2.expected_sequences[0][0].stable_min_lim == 15
    assert [s.name for s in group2.default_states] == ["NO_LIBRA", "EMPTY"]
    # Базовый профиль не изменился
    assert default.states[0].stable_min_lim == 25
    assert config.profile_ids_map == {"default": (), "group1": (101, 102, 103), "group2": (201, 202)}


def test_own_sequences_replace_inherited():
    builder = base_builder()
    builder.new_profile("other").add_exp_seq(("FULL", "EMPTY"))
    config = builder.build()
    assert seq_names(config.get_profile("other")) == [["FULL", "EMPTY"]]


def test_set_exp_seqs_accepts_single_and_many_sequences():
    builder = base_builder()
    builder.get_profile("default").set_exp_seqs([("EMPTY", "FULL"), (0, 1, 0)])
    assert seq_names(builder.build().get_profile("default")) == [["EMPTY", "FULL"], ["EMPTY", "FULL", "EMPTY"]]


def test_individual_mode_profiles_have_own_states():
    builder = FsmConfigBuilder()
    builder.set_states_mode("individual")
    a = builder.new_profile("a", default=True)
    a.new_state(cls_id=0, name="EMPTY", stable_min_lim=1)
    a.set_init_states(0)
    b = builder.new_profile("b")
    b.new_state(cls_id=5, name="OTHER", stable_min_lim=1)
    b.set_init_states("OTHER")
    config = builder.build()
    assert set(config.get_profile("b").states) == {5}
    assert set(config.state_configs) == {0, 5}


def test_equal_mode_rejects_new_states_in_derived_profile():
    builder = base_builder()
    builder.new_profile("other").new_state(cls_id=9, name="EXTRA")
    with pytest.raises(ValueError, match="equal"):
        builder.build()


def test_redeclare_inherited_state_is_error():
    builder = base_builder()
    builder.new_profile("other").new_state(cls_id=0, name="EMPTY")
    with pytest.raises(ValueError, match="update_state"):
        builder.build()


def test_unknown_state_reference_is_error():
    builder = base_builder()
    builder.new_profile("other").update_state("MISSING", stable_min_lim=1)
    with pytest.raises(ValueError, match="MISSING"):
        builder.build()


def test_single_profile_is_default_automatically():
    builder = FsmConfigBuilder()
    profile = builder.new_profile("only")
    profile.new_state(cls_id=0, name="EMPTY")
    profile.set_init_states(0)
    assert builder.build().def_profile == "only"


def test_default_profile_required_for_several_profiles():
    builder = FsmConfigBuilder()
    builder.set_states_mode("individual")
    for name in ("a", "b"):
        p = builder.new_profile(name)
        p.new_state(cls_id=0, name="EMPTY")
        p.set_init_states(0)
    with pytest.raises(ValueError, match="Default profile"):
        builder.build()
    builder.set_default_profile("B")
    assert builder.build().def_profile == "b"


def test_init_states_required():
    builder = FsmConfigBuilder()
    builder.new_profile("p").new_state(cls_id=0, name="EMPTY")
    with pytest.raises(ValueError, match="init"):
        builder.build()


def test_no_profiles_is_error():
    with pytest.raises(ValueError):
        FsmConfigBuilder().build()


def test_duplicate_profile_and_state_names():
    builder = base_builder()
    with pytest.raises(ValueError):
        builder.new_profile("DEFAULT")
    profile = builder.get_profile("default")
    with pytest.raises(ValueError):
        profile.new_state(cls_id=10, name="EMPTY")
    with pytest.raises(ValueError):
        profile.new_state(cls_id=0, name="NEW")


def test_update_state_cannot_change_identity():
    profile = ProfileConfigBuilder("p")
    with pytest.raises(ValueError):
        profile.update_state("EMPTY", name="OTHER")
    with pytest.raises(ValueError):
        profile.update_state("EMPTY")


def test_by_mapped_id_requires_ids():
    builder = base_builder(strategy=ProfileSwitcherStrategies.BY_MAPPED_ID)
    with pytest.raises(ValueError, match="mapped IDs"):
        builder.build()


def test_duplicate_mapped_ids_are_error():
    builder = make_builder()
    builder.set_profile_ids_map({"group2": [101]})
    with pytest.raises(ValueError, match="Duplicate mapped id"):
        builder.build()


def test_ids_map_requires_existing_profile():
    builder = base_builder()
    with pytest.raises(ValueError):
        builder.set_profile_ids_map({"missing": [1]})
    with pytest.raises(ValueError):
        builder.set_profile_ids_map({"default": ["x"]})


def test_switcher_accepts_name():
    builder = base_builder()
    builder.set_switcher("mixed")
    assert builder.build().switcher_strategy == ProfileSwitcherStrategies.MIXED
    with pytest.raises(ValueError):
        builder.set_switcher("unknown")


def test_ready_profile_config_can_be_added():
    profile = ProfileConfig(name=ProfileNames.SINGLE)
    empty = profile.new_state(cls_id=0, name="EMPTY", stable_min_lim=1)
    profile.set_init_states([empty])
    builder = FsmConfigBuilder()
    builder.add_profile(profile, default=True)
    config = builder.build()
    assert config.def_profile == "single"
    assert config.get_profile("single") is profile


def test_profile_registry_helpers():
    builder = make_builder()
    assert builder.list_profiles() == ("default", "group1", "group2")
    assert builder.has_profile("Group1")
    builder.remove_profile("group2")
    assert not builder.has_profile("group2")
    with pytest.raises(KeyError):
        builder.remove_profile("group2")


@pytest.mark.parametrize("kwargs", [
    {"stable_min_lim": -2},
    {"threshold": 1.5},
    {"name": ""},
])
def test_state_config_ranges(kwargs):
    params = {"cls_id": 0, "name": "EMPTY", **kwargs}
    with pytest.raises(ValueError):
        StateConfig(**params)


def test_state_field_types_are_validated():
    builder = base_builder()
    builder.get_profile("default").update_state("EMPTY", resettable="yes")
    with pytest.raises(ValueError, match="resettable"):
        builder.build()


def test_alias_must_point_to_existing_state():
    builder = base_builder()
    builder.get_profile("default").update_state("UNKNOWN", alias_of=77)
    with pytest.raises(ValueError, match="alias"):
        builder.build()


def test_enabled_writer_requires_name():
    with pytest.raises(ValueError):
        base_builder().set_raw_history_writer(enable=True, name="")
