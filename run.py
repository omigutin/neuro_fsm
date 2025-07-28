# run.py — ручной запуск и примеры NeuroFSM

from rich.table import Table
from rich.console import Console
from rich import box

from src.neuro_fsm.core import FsmManager, Fsm
from tests.test_configs.state_cls_with_profiles_cfg import StateClsWithProfilesConfig

TEST_SEQUENCES = [
    ([1, 2, 3, 1], "SINGLE"),  # int-путь
    ([1, 2, 1], "SINGLE"),  # str-путь
    ([1, 2, 3, 1, 0, 0], "SINGLE"),  # шум после
    ([0, 1, 2, 3, 1], "SINGLE"),  # шум до
    ([1, 3, 2, 1], None),  # неверный порядок
    ([2, 1, 2, 3], None),  # не та последовательность
    ([1, 2], None),  # неполная
    ([1, 3, 0, 2, 1], "FULL_FIRST"),
    ([1, 3, 0, 2, 1, 3], "FULL_FIRST"),
    (['EMPTY', 'UNKNOWN', 'UNDEFINED', 'FULL', 'EMPTY'], "FULL_FIRST"),
    ([0, 1, 3, 0, 2, 1], "FULL_FIRST"),
    ([1, 0, 3, 2, 1], None),  # нарушен порядок
    ([1, 3, 0, 2], None),  # неполная
    ([1, 2, 1, 0], None),  # не тот маршрут
]


def main():
    console = Console()
    table = Table(title="FSM Profile Detection", box=box.MINIMAL_DOUBLE_HEAD)

    table.add_column("№", justify="center", style="cyan")
    table.add_column("Input Sequence", justify="left")
    table.add_column("Expected Profile", justify="center", style="green")
    table.add_column("Detected Profile", justify="center", style="magenta")
    table.add_column("Result", justify="center", style="bold")

    for i, (seq, expected_profile) in enumerate(TEST_SEQUENCES, 1):
        fsm_manager = FsmManager()
        fsm_manager._set_config(StateClsWithProfilesConfig())
        fsm: Fsm = fsm_manager.create_fsm()

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
