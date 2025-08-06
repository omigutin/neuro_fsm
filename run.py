# run.py — ручной запуск и примеры NeuroFSM
from typing import Optional

from rich.table import Table
from rich.console import Console
from rich import box

from neuro_fsm.models.result import FsmResult
from src.neuro_fsm.core import FsmManager, Fsm
from tests.test_configs.state_cls_with_profiles_cfg import (StateClsWithProfilesConfig,
                                                            TEST_SEQUENCES_FOR_DEFAULT,
                                                            TEST_SEQUENCES_FOR_GROUP1,
                                                            TEST_SEQUENCES_FOR_GROUP2)


def main():
    console = Console()
    table = Table(title="FSM Profile Detection", box=box.MINIMAL_DOUBLE_HEAD)

    table.add_column("№", justify="center", style="cyan")
    table.add_column("Input Sequence", justify="left")
    table.add_column("Expected Profile", justify="center", style="green")
    table.add_column("Detected Profile", justify="center", style="magenta")
    table.add_column("Result", justify="center", style="bold")

    fsm_manager = FsmManager(StateClsWithProfilesConfig)
    fsm: Fsm = fsm_manager.create_fsm()

    fsm.switch_profile_by_pid(None)
    process_sequences(fsm, table, TEST_SEQUENCES_FOR_DEFAULT)

    fsm.switch_profile_by_pid(102)
    process_sequences(fsm, table, TEST_SEQUENCES_FOR_GROUP1)

    fsm.switch_profile_by_pid(202)
    process_sequences(fsm, table, TEST_SEQUENCES_FOR_GROUP2)

    console.print(table)

def process_sequences(fsm, table, sequences):
    for i, (seq, expected_profile) in enumerate(sequences, 1):
        result: Optional[FsmResult] = None

        for cls_id in seq:
            result = fsm.process_state(cls_id)

        detected_profile = result.active_profile if result.active_profile else None
        success = detected_profile.upper() == expected_profile.upper()
        table.add_row(
            str(i),
            str(seq),
            str(expected_profile),
            str(detected_profile),
            "[green]✔[/green]" if success else "[red]✘[/red]"
        )


if __name__ == "__main__":
    main()
