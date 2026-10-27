# neuro_fsm

[Русская версия](README.ru.md)

NeuroFSM is a lightweight finite state machine for neural network inference pipelines. It turns a stream of per-frame class predictions into robust events: a state became stable, a cycle (expected sequence of states) completed, the active profile changed.

A typical use case is counting "empty → full → empty" cycles in a camera work zone while suppressing single-frame noise.

## Installation

```bash
poetry add git+https://github.com/omigutin/neuro_fsm.git
# or
pip install git+https://github.com/omigutin/neuro_fsm.git
```

Python ≥ 3.10, no runtime dependencies.

## Quick start

```python
from neuro_fsm import FsmConfigBuilder, FsmManager, ProfileSwitcherStrategies

builder = FsmConfigBuilder()
builder.set_switcher(ProfileSwitcherStrategies.BY_MAPPED_ID)

# Base profile declares all states
base = builder.new_profile("default", default=True)
base.new_state(cls_id=0, name="EMPTY", stable_min_lim=25, resettable=True, reset_trigger=True)
base.new_state(cls_id=1, name="FULL", stable_min_lim=50, resettable=False, reset_trigger=True)
base.new_state(cls_id=2, name="NO_LIBRA", stable_min_lim=10, break_trigger=True)
base.new_state(cls_id=3, name="UNKNOWN")
base.set_init_states("EMPTY")
base.set_def_states("UNKNOWN")
base.set_exp_seqs(("EMPTY", "FULL", "EMPTY"))

# Derived profile inherits states and overrides only what differs
group1 = builder.new_profile("group1")
group1.update_state("EMPTY", stable_min_lim=5)
group1.update_state("FULL", stable_min_lim=10)

builder.set_profile_ids_map({"group1": [101, 102, 103]})

manager = FsmManager(builder)          # accepts FsmConfigBuilder, FsmConfig, dict, class or module
fsm = manager.create_fsm()             # one FSM per prediction stream (e.g. per work zone)

fsm.switch_profile_by_pid(102)         # profile by product id; unknown id → default profile
for cls_id in predictions:             # class id from the network; None/unknown → default state
    result = fsm.process_state(cls_id)
    if result.breaker:
        ...                            # interrupt zone processing
    if result.stage_done:
        counter += 1                   # EMPTY → FULL → EMPTY cycle completed
```

## How it works

On every `process_state(cls_id)` call:

1. The state is passed to **all** profiles; each keeps its own counters and history, so switching profiles mid-cycle loses nothing.
2. If the current state is a reset trigger (`reset_trigger`), counters of `resettable` states (except the current one) are reset.
3. When a state's counter reaches exactly `stable_min_lim`, the state becomes **stable**: it is appended to the history (if different from the last one) and other counters are reset. `stable_min_lim` of `None`, `-1` or `0` means "never stable".
4. If the active profile's history ends with one of `expected_sequences`, the result has `stage_done=True` and all profiles are reset to their init states.
5. Otherwise the switching strategy may change the active profile.

`FsmResult` is an immutable step snapshot: `active_profile`, `prev_profile`, `state`, `resetter`, `breaker`, `stable`, `stage_done`, `profile_changed`, `counters`, `history`, `step_index`, `timestamp`. `to_dict()` returns plain types.

`fsm.profile` is a read-only view of the active profile (`name`, `cur_state`, `history`, `counters`, `get_threshold(cls_id)`, `is_breaker(cls_id)`, etc.).

## Profiles and strategies

| Strategy | Behaviour |
|---|---|
| `SINGLE` | No automatic switching; manual via `switch_profile_by_name()`. |
| `BY_MAPPED_ID` | Manual selection by external id: `switch_profile_by_pid(pid)`. Unknown id or `None` → default profile. |
| `BY_MATCH` | Switch to a profile that completed an expected sequence (the cycle is counted). |
| `BY_EXCLUSION` | Switch when only one profile can still complete a sequence. |
| `MIXED` | `BY_MATCH` first, then `BY_EXCLUSION`. |

Builder states modes (`set_states_mode`):

- `"equal"` (default) — states are declared in the default profile; other profiles inherit states, init/default states and sequences and tune parameters with `update_state()`. Their own `add_exp_seq()`/`set_exp_seqs()` replace inherited sequences.
- `"individual"` — every profile declares its own states.

State references accept a `cls_id`, a name, an Enum member (matched by name) or a `StateConfig`. The config is validated in `build()`; errors are raised as `ValueError`/`TypeError`.

## Compatible config formats

`FsmManager` also accepts a dict / class / module (keys are case-insensitive).

Simple format (as used in `pc_develop`):

```python
class StateMachineConfig:
    ENABLE = True
    STATES = (State(cls_id=0, name="EMPTY", stable_min_lim=5, resettable=True), ...)  # StateConfig, dict or object with cls_id/name
    EXPECTED_SEQUENCES = ((NNetClasses.EMPTY, NNetClasses.FULL, NNetClasses.EMPTY),)  # Enum refs are matched by name
    INIT_STATE = 0          # or INIT_STATES
    DEFAULT_STATE = 3       # or DEFAULT_STATES
```

Profiles format:

```python
CONFIG = {
    "ENABLE": True,
    "STATES": [{"cls_id": 0, "name": "EMPTY", "stable_min_lim": 25}, ...],
    "STATE_PROFILES": [
        {"name": "group1", "states": {"EMPTY": {"stable_min_lim": 5}},
         "expected_sequences": [["EMPTY", "FULL", "EMPTY"]], "init_states": "EMPTY", "default_states": "UNKNOWN"},
        {"name": "default", "expected_sequences": [["EMPTY", "FULL", "EMPTY"]], "init_states": "EMPTY"},
    ],
    "PROFILE_SWITCHER_STRATEGY": "BY_MAPPED_ID",
    "DEFAULT_PROFILE": "default",
    "PROFILE_IDS_MAP": {"group1": [101, 102], "default": []},
}
```

If `ENABLE` is false, the rest is not parsed and a disabled config is created (`process_state` returns an empty result). Unknown keys go to `config.meta`.

## History logs

Disabled by default. When enabled, files are written to `./fsm_logs`; files older than `max_age_days` are removed:

```python
builder.set_raw_history_writer(enable=True, name="{timestamp}_raw.txt")
builder.set_stable_history_writer(enable=True, name="{timestamp}_stable.yaml")
```

In dict configs use `RAW_HISTORY_WRITER` / `STABLE_HISTORY_WRITER` with `enable`, `name`, `max_age_days`. Logs are written on every frame, so enable them for debugging. `manager.destroy()` or `fsm.close()` closes the files.

## Development

```bash
poetry install
poetry run pytest          # tests
poetry run python run.py   # reference sequences table
```

## License

MIT
