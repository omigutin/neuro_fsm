""" Логика одного профиля: стабильность, сбросы, история, завершение последовательности. """
import pytest

from neuro_fsm import FsmConfigBuilder, FsmManager, FsmResult
from tests.helpers import EMPTY, FULL, NO_LIBRA, UNKNOWN, base_builder, count_done, make_fsm, run


def names(states) -> list[str]:
    return [s.name for s in states]


def test_state_becomes_stable_exactly_at_limit():
    fsm = make_fsm(base_builder(empty_lim=3))
    results = run(fsm, [EMPTY] * 5)
    assert [r.stable for r in results] == [False, False, True, False, False]


def test_full_cycle_sets_stage_done_and_resets_history():
    fsm = make_fsm(base_builder())
    results = run(fsm, [EMPTY] * 3 + [FULL] * 3 + [EMPTY] * 3)
    assert count_done(results) == 1
    last = results[-1]
    assert last.stage_done
    assert names(last.history) == ["EMPTY", "FULL", "EMPTY"]
    # После срабатывания история сброшена к стартовой
    assert names(fsm.profile.history) == ["EMPTY"]
    assert all(count == 0 for count in fsm.profile.counters.values())


def test_consecutive_cycles_are_counted():
    fsm = make_fsm(base_builder())
    cycle = [EMPTY] * 3 + [FULL] * 3 + [EMPTY] * 3
    assert count_done(run(fsm, cycle + cycle[3:] + cycle[3:])) == 3


def test_short_full_does_not_complete_cycle():
    fsm = make_fsm(base_builder(full_lim=5))
    assert count_done(run(fsm, [EMPTY] * 3 + [FULL] * 4 + [EMPTY] * 3)) == 0


def test_resetter_resets_only_resettable_counters():
    fsm = make_fsm(base_builder(empty_lim=10, full_lim=10))
    run(fsm, [EMPTY, EMPTY, FULL, FULL])
    # FULL — триггер сброса: счётчик EMPTY (сбрасываемый) обнулён
    assert fsm.profile.get_counter(EMPTY) == 0
    assert fsm.profile.get_counter(FULL) == 2
    run(fsm, [EMPTY])
    # EMPTY — триггер сброса, но FULL не сбрасываемый
    assert fsm.profile.get_counter(FULL) == 2
    assert fsm.profile.get_counter(EMPTY) == 1


def test_stable_state_resets_other_counters():
    fsm = make_fsm(base_builder(empty_lim=3, full_lim=10))
    run(fsm, [FULL, FULL, EMPTY, EMPTY, EMPTY])
    assert fsm.profile.get_counter(FULL) == 0
    assert fsm.profile.get_counter(EMPTY) == 3


def test_noise_inside_stable_state_does_not_break_cycle():
    fsm = make_fsm(base_builder(empty_lim=3, full_lim=4))
    sequence = [EMPTY] * 3 + [FULL, FULL, UNKNOWN, UNKNOWN, FULL, FULL] + [EMPTY] * 3
    assert count_done(run(fsm, sequence)) == 1


def test_breaker_and_resetter_flags():
    fsm = make_fsm(base_builder())
    result = fsm.process_state(NO_LIBRA)
    assert result.breaker and not result.resetter
    result = fsm.process_state(FULL)
    assert result.resetter and not result.breaker


@pytest.mark.parametrize("cls_id", [None, 42, -7])
def test_unknown_cls_id_uses_default_state(cls_id):
    fsm = make_fsm(base_builder())
    assert fsm.process_state(cls_id).state.name == "UNKNOWN"


def test_unknown_cls_id_without_default_state_raises():
    builder = FsmConfigBuilder()
    profile = builder.new_profile("p")
    profile.new_state(cls_id=0, name="EMPTY", stable_min_lim=1)
    profile.set_init_states(0)
    fsm = make_fsm(builder)
    with pytest.raises(KeyError):
        fsm.process_state(5)


def test_profile_without_sequences_never_completes():
    builder = FsmConfigBuilder()
    profile = builder.new_profile("p")
    profile.new_state(cls_id=0, name="EMPTY", stable_min_lim=1)
    profile.new_state(cls_id=1, name="FULL", stable_min_lim=1)
    profile.set_init_states(0)
    fsm = make_fsm(builder)
    results = run(fsm, [0, 1, 0, 1])
    assert count_done(results) == 0
    assert names(results[-1].history) == ["EMPTY", "FULL", "EMPTY", "FULL"]


def test_init_states_start_history():
    builder = base_builder()
    builder.get_profile("default").set_init_states(("NO_LIBRA", "EMPTY"))
    fsm = make_fsm(builder)
    assert names(fsm.profile.history) == ["NO_LIBRA", "EMPTY"]
    assert fsm.profile.cur_state.name == "EMPTY"


def test_reset_clears_progress_and_step_index():
    fsm = make_fsm(base_builder())
    run(fsm, [EMPTY] * 3 + [FULL] * 3)
    assert names(fsm.profile.history) == ["EMPTY", "FULL"]
    fsm.reset()
    assert fsm.result is None
    assert fsm.step_index == 0
    assert names(fsm.profile.history) == ["EMPTY"]
    assert fsm.process_state(EMPTY).step_index == 1


def test_disabled_fsm_returns_empty_result():
    builder = base_builder()
    builder.set_enable(False)
    fsm = make_fsm(builder)
    result = fsm.process_state(EMPTY)
    assert result.active_profile == "" and result.state is None and not result.stage_done
    with pytest.raises(RuntimeError):
        _ = fsm.profile


def test_result_to_dict_is_serializable():
    fsm = make_fsm(base_builder())
    data = fsm.process_state(EMPTY).to_dict()
    assert data["state"] == "EMPTY" and data["cls_id"] == EMPTY
    assert data["counters"]["EMPTY"] == 1
    assert data["history"] == ["EMPTY"]
    assert isinstance(data["timestamp"], str)


def test_result_is_immutable():
    result = make_fsm(base_builder()).process_state(EMPTY)
    assert isinstance(result, FsmResult)
    with pytest.raises(AttributeError):
        result.stage_done = True  # type: ignore[misc]


def test_profile_view_is_read_only():
    fsm = make_fsm(base_builder())
    view = fsm.profile
    with pytest.raises(AttributeError):
        view.name = "x"  # type: ignore[misc]
    assert not hasattr(view, "reset_counters")
    assert view.get_threshold(999) is None
    assert view.is_breaker(NO_LIBRA)
    assert view.expected_sequences_names == (("EMPTY", "FULL", "EMPTY"),)
    assert view.default_state.name == "UNKNOWN"


def test_threshold_from_config():
    builder = base_builder()
    builder.get_profile("default").update_state("FULL", threshold=0.7)
    manager = FsmManager(builder)
    fsm = manager.create_fsm()
    assert fsm.profile.get_threshold(FULL) == 0.7
    assert fsm.profile.get_threshold(EMPTY) is None
    assert manager.config.get_state_threshold_by_cls_id(FULL) == 0.7


def test_states_equal_by_cls_id_and_name_across_profiles():
    builder = base_builder()
    builder.new_profile("other").update_state("EMPTY", stable_min_lim=1)
    manager = FsmManager(builder)
    fsm = manager.create_fsm()
    state_default = fsm.profile.get_state(EMPTY)
    fsm.switch_profile_by_name("other")
    state_other = fsm.profile.get_state(EMPTY)
    assert state_default.stable_min_lim != state_other.stable_min_lim
    assert state_default == state_other
    assert hash(state_default) == hash(state_other)
