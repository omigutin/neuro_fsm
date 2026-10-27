""" FsmManager и писатели истории. """
import asyncio
import os
import time

import pytest

from neuro_fsm import FsmManager, HistoryWriterConfig
from neuro_fsm.history_writer import AsyncRawHistoryWriter, AsyncStableHistoryWriter, RawHistoryWriter
from tests.helpers import EMPTY, FULL, base_builder, run
from tests.test_configs.state_cls_with_profiles_cfg import make_builder


def test_manager_accepts_builder_config_and_dict():
    builder = base_builder()
    config = builder.build()
    assert FsmManager(builder).enable
    assert FsmManager(config).config is config
    assert FsmManager({"STATES": [{"cls_id": 0, "name": "EMPTY"}], "INIT_STATE": 0}).enable


def test_manager_without_config():
    manager = FsmManager()
    assert not manager.enable
    with pytest.raises(RuntimeError):
        manager.create_fsm()


def test_manager_batch_operations():
    manager = FsmManager(make_builder())
    fsm1, fsm2 = manager.create_fsm(), manager.create_fsm()
    assert len(manager) == 2 and manager[0] is fsm1 and list(manager) == [fsm1, fsm2]

    manager.switch_profile_by_pid(201)
    assert manager.get_statuses() == {0: "group2", 1: "group2"}
    manager.switch_profile_by_name("group1")
    manager.update_all(EMPTY)
    assert fsm1.step_index == fsm2.step_index == 1
    manager.reset_all()
    assert fsm1.step_index == 0 and fsm1.profile.name == "group1"
    manager.destroy()
    assert len(manager) == 0 and manager.config is None


def test_create_fsm_with_individual_config_keeps_manager_config():
    manager = FsmManager(make_builder())
    fsm = manager.create_fsm(base_builder())
    assert fsm.profile_names == ("default",)
    assert len(manager.config.profile_configs) == 3


def test_writers_disabled_by_default_create_no_files():
    fsm = FsmManager(base_builder()).create_fsm()
    run(fsm, [EMPTY] * 3)
    assert not os.path.exists("fsm_logs")


def test_enabled_writers_write_logs():
    builder = base_builder()
    builder.set_raw_history_writer(enable=True, name="{timestamp}_raw.txt")
    builder.set_stable_history_writer(enable=True, name="{timestamp}_stable.yaml")
    manager = FsmManager(builder)
    fsm = manager.create_fsm()
    run(fsm, [EMPTY] * 3 + [FULL] * 3 + [EMPTY] * 3)
    manager.destroy()

    files = sorted(os.listdir("fsm_logs"))
    raw = next(f for f in files if f.endswith("_raw.txt"))
    stable = next(f for f in files if f.endswith("_stable.yaml"))
    with open(os.path.join("fsm_logs", raw), encoding="utf-8") as f:
        assert f.read().split() == ["0"] * 3 + ["1"] * 3 + ["0"] * 3
    with open(os.path.join("fsm_logs", stable), encoding="utf-8") as f:
        text = f.read()
    for marker in ("FSM_CONFIGURATION:", "PROFILES_CONFIGURATION:", "EVENTS:", "EXPECTED_SEQ_DONE", "RUNTIME:"):
        assert marker in text


def test_old_log_files_are_removed():
    os.makedirs("fsm_logs")
    old_file = os.path.join("fsm_logs", "old_raw.txt")
    fresh_file = os.path.join("fsm_logs", "fresh_raw.txt")
    for path in (old_file, fresh_file):
        with open(path, "w", encoding="utf-8") as f:
            f.write("0")
    month_ago = time.time() - 30 * 24 * 3600
    os.utime(old_file, (month_ago, month_ago))
    RawHistoryWriter(HistoryWriterConfig(name="new_raw.txt", enable=True, max_age_days=14))
    assert not os.path.exists(old_file)
    assert os.path.exists(fresh_file)


def test_async_writers():
    pytest.importorskip("aiofiles")
    fsm = FsmManager(base_builder()).create_fsm()
    run(fsm, [EMPTY] * 3)
    profiles = fsm._profile_manager.profiles  # noqa: SLF001 — доступ к рабочим профилям для писателя
    active = fsm._profile_manager.active_profile  # noqa: SLF001

    raw = AsyncRawHistoryWriter(HistoryWriterConfig(name="a_raw.txt", enable=True, fields=("cls_id", "state")))
    stable = AsyncStableHistoryWriter(HistoryWriterConfig(name="a_stable.yaml", enable=True))

    async def write() -> None:
        await raw.write({"cls_id": 0, "state": "EMPTY", "ignored": 1})
        await stable.write_configs({"enable": True})
        await stable.write_profile_configs(profiles)
        await stable.write_event(timestamp=1.5, active_profile=active, state=active.cur_state, frame_number=7)

    asyncio.run(write())
    with open(raw.path, encoding="utf-8") as f:
        assert f.read() == "cls_id=0; state=EMPTY\n"
    with open(stable.path, encoding="utf-8") as f:
        text = f.read()
    assert "PROFILE_NAME: 'default'" in text and "frame=7" in text and "history: [EMPTY, ]" in text
