""" Общие помощники тестов. """
from typing import Iterable, Optional

from neuro_fsm import FsmConfigBuilder, Fsm, FsmManager, FsmResult, ProfileSwitcherStrategies

EMPTY, FULL, NO_LIBRA, UNKNOWN = 0, 1, 2, 3


def base_builder(
        strategy: ProfileSwitcherStrategies = ProfileSwitcherStrategies.SINGLE,
        empty_lim: int = 3,
        full_lim: int = 3,
) -> FsmConfigBuilder:
    """ Минимальная конфигурация: один профиль 'default' с циклом EMPTY → FULL → EMPTY. """
    builder = FsmConfigBuilder()
    builder.set_switcher(strategy)
    profile = builder.new_profile("default", default=True)
    profile.new_state(cls_id=EMPTY, name="EMPTY", stable_min_lim=empty_lim, resettable=True, reset_trigger=True)
    profile.new_state(cls_id=FULL, name="FULL", stable_min_lim=full_lim, resettable=False, reset_trigger=True)
    profile.new_state(cls_id=NO_LIBRA, name="NO_LIBRA", stable_min_lim=2, break_trigger=True)
    profile.new_state(cls_id=UNKNOWN, name="UNKNOWN")
    profile.set_init_states("EMPTY")
    profile.set_def_states("UNKNOWN")
    profile.set_exp_seqs(("EMPTY", "FULL", "EMPTY"))
    return builder


def run(fsm: Fsm, sequence: Iterable[Optional[int]]) -> list[FsmResult]:
    """ Прогоняет последовательность и возвращает все результаты. """
    return [fsm.process_state(cls_id) for cls_id in sequence]


def count_done(results: list[FsmResult]) -> int:
    return sum(r.stage_done for r in results)


def make_fsm(builder: FsmConfigBuilder) -> Fsm:
    """ FSM из билдера. """
    return FsmManager(builder).create_fsm()
