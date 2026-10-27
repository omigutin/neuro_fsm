""" Переключение профилей: вручную и по стратегиям. """
import pytest

from neuro_fsm import FsmManager, ProfileNames, ProfileSwitcherStrategies
from tests.helpers import EMPTY, FULL, UNKNOWN, base_builder, count_done, make_fsm, run
from tests.test_configs.state_cls_with_profiles_cfg import TEST_CASES, make_builder

S = ProfileSwitcherStrategies


@pytest.mark.parametrize("pid, sequence, expected_profile, expected_cycles", TEST_CASES)
def test_reference_cases(pid, sequence, expected_profile, expected_cycles):
    fsm = FsmManager(make_builder()).create_fsm()
    fsm.switch_profile_by_pid(pid)
    assert count_done(run(fsm, sequence)) == expected_cycles
    assert fsm.profile.name == expected_profile


def test_switch_by_pid_and_fallback_to_default():
    fsm = FsmManager(make_builder()).create_fsm()
    assert fsm.switch_profile_by_pid(201) is True
    assert fsm.profile.name == "group2"
    assert fsm.switch_profile_by_pid(202) is False
    fsm.switch_profile_by_pid(None)
    assert fsm.profile.name == ProfileNames.DEFAULT.value
    fsm.switch_profile_by_pid(101)
    fsm.switch_profile_by_pid(12345)
    assert fsm.profile.name == "default"


def test_switch_by_name_case_insensitive_and_unknown():
    fsm = FsmManager(make_builder()).create_fsm()
    fsm.switch_profile_by_name("GROUP1")
    assert fsm.profile.name == "group1"
    fsm.switch_profile_by_name(ProfileNames.DEFAULT)
    assert fsm.profile.name == "default"
    with pytest.raises(ValueError):
        fsm.switch_profile_by_name("nope")


def test_manual_switch_is_reported_in_next_result():
    fsm = FsmManager(make_builder()).create_fsm()
    assert not fsm.process_state(EMPTY).profile_changed
    fsm.switch_profile_by_pid(101)
    result = fsm.process_state(EMPTY)
    assert result.profile_changed and result.prev_profile == "default" and result.active_profile == "group1"
    result = fsm.process_state(EMPTY)
    assert not result.profile_changed and result.prev_profile is None


def test_profiles_are_tracked_in_parallel():
    """ Неактивный профиль накапливает свою историю, поэтому переключение посреди цикла его не теряет. """
    fsm = FsmManager(make_builder()).create_fsm()
    run(fsm, [EMPTY] * 5 + [FULL] * 10)
    fsm.switch_profile_by_pid(101)
    assert [s.name for s in fsm.profile.history] == ["EMPTY", "FULL"]
    assert count_done(run(fsm, [EMPTY] * 5)) == 1


def _two_profile_builder(strategy: S):
    """ default: долгие пороги; fast: короткие пороги. """
    builder = base_builder(strategy=strategy, empty_lim=5, full_lim=5)
    fast = builder.new_profile("fast")
    fast.update_state("EMPTY", stable_min_lim=2)
    fast.update_state("FULL", stable_min_lim=2)
    return builder


@pytest.mark.parametrize("strategy", [S.SINGLE, S.BY_MAPPED_ID])
def test_no_auto_switch_for_manual_strategies(strategy):
    builder = _two_profile_builder(strategy)
    if strategy == S.BY_MAPPED_ID:
        builder.set_profile_ids_map({"fast": [1]})
    fsm = make_fsm(builder)
    results = run(fsm, [EMPTY] * 2 + [FULL] * 2 + [EMPTY] * 2)
    assert fsm.profile.name == "default"
    assert count_done(results) == 0


@pytest.mark.parametrize("strategy", [S.BY_MATCH, S.MIXED])
def test_by_match_switches_to_completed_profile(strategy):
    fsm = make_fsm(_two_profile_builder(strategy))
    results = run(fsm, [EMPTY] * 2 + [FULL] * 2 + [EMPTY] * 2)
    last = results[-1]
    assert last.profile_changed and last.prev_profile == "default" and last.active_profile == "fast"
    # Профиль выбран потому, что завершил последовательность — цикл засчитан
    assert last.stage_done and count_done(results) == 1


def test_by_match_keeps_active_profile_when_it_completes():
    fsm = make_fsm(_two_profile_builder(S.BY_MATCH))
    fsm.switch_profile_by_name("fast")
    results = run(fsm, [EMPTY] * 2 + [FULL] * 2 + [EMPTY] * 2)
    assert fsm.profile.name == "fast" and count_done(results) == 1
    assert not any(r.profile_changed for r in results[1:])


def test_by_exclusion_switches_to_only_possible_profile():
    builder = base_builder(strategy=S.BY_EXCLUSION, empty_lim=2, full_lim=2)
    other = builder.new_profile("unknown_first")
    other.set_exp_seqs(("EMPTY", "UNKNOWN", "FULL", "EMPTY"))
    builder.get_profile("default").update_state("UNKNOWN", stable_min_lim=2)
    fsm = make_fsm(builder)
    # EMPTY → UNKNOWN: для 'default' (EMPTY, FULL, EMPTY) продолжение невозможно
    results = run(fsm, [EMPTY] * 2 + [UNKNOWN] * 2)
    assert results[-1].profile_changed and fsm.profile.name == "unknown_first"
    assert count_done(run(fsm, [FULL] * 2 + [EMPTY] * 2)) == 1


def test_by_exclusion_does_not_switch_when_several_possible():
    builder = _two_profile_builder(S.BY_EXCLUSION)
    fsm = make_fsm(builder)
    run(fsm, [EMPTY] * 5 + [FULL] * 5)
    assert fsm.profile.name == "default"
