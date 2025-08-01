# run.py — ручной запуск и примеры NeuroFSM

from rich.table import Table
from rich.console import Console
from rich import box

from src.neuro_fsm.core import FsmManager, Fsm
from tests.test_configs.state_cls_with_profiles_cfg import StateClsWithProfilesConfig, TEST_SEQUENCES


def main():
    console = Console()
    table = Table(title="FSM Profile Detection", box=box.MINIMAL_DOUBLE_HEAD)

    table.add_column("№", justify="center", style="cyan")
    table.add_column("Input Sequence", justify="left")
    table.add_column("Expected Profile", justify="center", style="green")
    table.add_column("Detected Profile", justify="center", style="magenta")
    table.add_column("Result", justify="center", style="bold")

    for i, (seq, expected_profile) in enumerate(TEST_SEQUENCES, 1):
        fsm_manager = FsmManager(StateClsWithProfilesConfig)
        fsm: Fsm = fsm_manager.create()

        for cls in seq:
            fsm.process_state(cls)

        detected = fsm.active_profile.name if fsm.active_profile else None
        success = detected == expected_profile
        table.add_row(
            str(i),
            str(seq),
            str(expected_profile),
            str(detected),
            "[green]✔[/green]" if success else "[red]✘[/red]"
        )

    console.print(table)


if __name__ == "__main__":
    main()
