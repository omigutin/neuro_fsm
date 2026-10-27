# neuro_fsm

[English version](README.md)

NeuroFSM — лёгкая машина состояний для пайплайнов инференса нейросетей. Она превращает поток покадровых предсказаний классов в устойчивые события: состояние стало стабильным, цикл (ожидаемая последовательность состояний) завершился, профиль сменился.

Типичная задача — подсчёт циклов «пусто → полно → пусто» в рабочей зоне камеры с подавлением шума отдельных кадров.

## Установка

```bash
poetry add git+https://github.com/omigutin/neuro_fsm.git
# или
pip install git+https://github.com/omigutin/neuro_fsm.git
```

Python ≥ 3.10, без runtime-зависимостей.

## Быстрый старт

```python
from neuro_fsm import FsmConfigBuilder, FsmManager, ProfileSwitcherStrategies

builder = FsmConfigBuilder()
builder.set_switcher(ProfileSwitcherStrategies.BY_MAPPED_ID)

# Базовый профиль: здесь объявляются все состояния
base = builder.new_profile("default", default=True)
base.new_state(cls_id=0, name="EMPTY", stable_min_lim=25, resettable=True, reset_trigger=True)
base.new_state(cls_id=1, name="FULL", stable_min_lim=50, resettable=False, reset_trigger=True)
base.new_state(cls_id=2, name="NO_LIBRA", stable_min_lim=10, break_trigger=True)
base.new_state(cls_id=3, name="UNKNOWN")
base.set_init_states("EMPTY")
base.set_def_states("UNKNOWN")
base.set_exp_seqs(("EMPTY", "FULL", "EMPTY"))

# Профиль наследует состояния и меняет только нужные параметры
group1 = builder.new_profile("group1")
group1.update_state("EMPTY", stable_min_lim=5)
group1.update_state("FULL", stable_min_lim=10)

builder.set_profile_ids_map({"group1": [101, 102, 103]})

manager = FsmManager(builder)          # принимает FsmConfigBuilder, FsmConfig, dict, класс или модуль
fsm = manager.create_fsm()             # одна FSM на поток предсказаний (например, на рабочую зону)

fsm.switch_profile_by_pid(102)         # профиль по id продукции; неизвестный id → профиль по умолчанию
for cls_id in predictions:             # cls_id от нейросети; None/неизвестный → состояние по умолчанию
    result = fsm.process_state(cls_id)
    if result.breaker:
        ...                            # прервать обработку зоны
    if result.stage_done:
        counter += 1                   # цикл EMPTY → FULL → EMPTY завершён
```

## Как это работает

На каждом шаге `process_state(cls_id)`:

1. Состояние передаётся **всем** профилям: у каждого свои счётчики и история, поэтому смена профиля посреди цикла ничего не теряет.
2. Если текущее состояние — триггер сброса (`reset_trigger`), обнуляются счётчики сбрасываемых (`resettable`) состояний, кроме текущего.
3. Когда счётчик состояния ровно достигает `stable_min_lim`, состояние становится **стабильным**: оно добавляется в историю (если отличается от последнего), остальные счётчики обнуляются. `stable_min_lim` равный `None`, `-1` или `0` означает «никогда не стабильно».
4. Если история активного профиля заканчивается одной из `expected_sequences`, результат получает `stage_done=True`, и все профили сбрасываются к стартовым состояниям.
5. Иначе стратегия может автоматически сменить активный профиль.

`FsmResult` — неизменяемый снимок шага: `active_profile`, `prev_profile`, `state`, `resetter`, `breaker`, `stable`, `stage_done`, `profile_changed`, `counters`, `history`, `step_index`, `timestamp`. `to_dict()` возвращает словарь из простых типов.

`fsm.profile` — read-only представление активного профиля (`name`, `cur_state`, `history`, `counters`, `get_threshold(cls_id)`, `is_breaker(cls_id)` и т.д.).

## Профили и стратегии

| Стратегия | Поведение |
|---|---|
| `SINGLE` | Автоматического переключения нет; вручную — `switch_profile_by_name()`. |
| `BY_MAPPED_ID` | Профиль выбирается вручную по внешнему id: `switch_profile_by_pid(pid)`. Неизвестный id или `None` → профиль по умолчанию. |
| `BY_MATCH` | Переключение на профиль, завершивший ожидаемую последовательность (цикл засчитывается). |
| `BY_EXCLUSION` | Переключение, если последовательность ещё возможна только у одного профиля. |
| `MIXED` | Сначала `BY_MATCH`, затем `BY_EXCLUSION`. |

Режимы состояний билдера (`set_states_mode`):

- `"equal"` (по умолчанию) — состояния объявляются в профиле по умолчанию; остальные профили наследуют состояния, init/default состояния и последовательности и меняют параметры через `update_state()`. Собственные `add_exp_seq()`/`set_exp_seqs()` заменяют унаследованные последовательности.
- `"individual"` — каждый профиль объявляет свои состояния.

Все ссылки на состояния принимают `cls_id`, имя, член Enum (по имени) или `StateConfig`. Конфигурация проверяется в `build()`; ошибки выбрасываются как `ValueError`/`TypeError` с описанием на английском.

## Совместимые форматы конфигурации

`FsmManager` принимает и dict/класс/модуль (регистр ключей не важен).

Простой формат (как в `pc_develop`):

```python
class StateMachineConfig:
    ENABLE = True
    STATES = (State(cls_id=0, name="EMPTY", stable_min_lim=5, resettable=True), ...)  # StateConfig, dict или объект с cls_id/name
    EXPECTED_SEQUENCES = ((NNetClasses.EMPTY, NNetClasses.FULL, NNetClasses.EMPTY),)  # Enum-ссылки ищутся по имени
    INIT_STATE = 0          # или INIT_STATES
    DEFAULT_STATE = 3       # или DEFAULT_STATES
```

Формат с профилями:

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

Если `ENABLE` ложно, остальные поля не разбираются и создаётся выключенная конфигурация (`process_state` возвращает пустой результат). Нераспознанные ключи попадают в `config.meta`.

## Логи истории

По умолчанию выключены. При включении файлы пишутся в `./fsm_logs`, файлы старше `max_age_days` удаляются:

```python
builder.set_raw_history_writer(enable=True, name="{timestamp}_raw.txt")
builder.set_stable_history_writer(enable=True, name="{timestamp}_stable.yaml")
```

В формате dict — ключи `RAW_HISTORY_WRITER` / `STABLE_HISTORY_WRITER` с полями `enable`, `name`, `max_age_days`. Логи пишутся на каждом кадре, поэтому включать их стоит для отладки. `manager.destroy()` или `fsm.close()` закрывают файлы.

## Разработка

```bash
poetry install
poetry run pytest          # тесты
poetry run python run.py   # таблица прогона эталонных последовательностей
```

## Лицензия

MIT
