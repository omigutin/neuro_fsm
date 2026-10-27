""" Ручной запуск: прогон тестовых последовательностей через FSM с выводом таблицы. """
from rich import box
from rich.console import Console
from rich.table import Table

from neuro_fsm import FsmManager
from tests.test_configs.state_cls_with_profiles_cfg import make_builder, TEST_CASES


def main() -> None:
    table = Table(title="NeuroFSM: test sequences", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("№", justify="center", style="cyan")
    table.add_column("pid", justify="center")
    table.add_column("Frames", justify="right")
    table.add_column("Profile", justify="center", style="magenta")
    table.add_column("Cycles (expected / done)", justify="center")
    table.add_column("Result", justify="center", style="bold")

    manager = FsmManager(make_builder())
    for i, (pid, sequence, expected_profile, expected_cycles) in enumerate(TEST_CASES, 1):
        fsm = manager.create_fsm()
        fsm.switch_profile_by_pid(pid)
        done = sum(fsm.process_state(cls_id).stage_done for cls_id in sequence)
        success = fsm.profile.name == expected_profile and done == expected_cycles
        table.add_row(
            str(i), str(pid), str(len(sequence)), fsm.profile.name, f"{expected_cycles} / {done}",
            "[green]✔[/green]" if success else "[red]✘[/red]",
        )
    manager.destroy()
    Console().print(table)


if __name__ == "__main__":
    main()
