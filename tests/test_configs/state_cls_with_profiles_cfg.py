""" Конфигурация через билдер: режим "equal", три профиля, переключение по внешнему id. """
from neuro_fsm import FsmConfigBuilder, ProfileConfigBuilder, ProfileSwitcherStrategies, ProfileNames


def make_builder() -> FsmConfigBuilder:
    """ Билдер тестовой конфигурации. """
    builder = FsmConfigBuilder()
    builder.set_states_mode("equal")
    builder.set_switcher(ProfileSwitcherStrategies.BY_MAPPED_ID)

    # Базовый профиль: здесь объявляются все состояния
    profile = builder.new_profile(ProfileNames.DEFAULT, default=True)
    profile.new_state(cls_id=0, name='EMPTY', stable_min_lim=25, resettable=True, reset_trigger=True)
    profile.new_state(cls_id=1, name='FULL', stable_min_lim=50, resettable=False, reset_trigger=True)
    profile.new_state(cls_id=2, name='NO_LIBRA', stable_min_lim=10, resettable=True, reset_trigger=True,
                      break_trigger=True)
    profile.new_state(cls_id=3, name='UNKNOWN', stable_min_lim=None, resettable=True)
    profile.set_init_states((2, 0))
    profile.set_def_states(3)
    profile.set_exp_seqs(('EMPTY', 'FULL', 'EMPTY'))

    # Наследники меняют только нужные параметры
    profile = builder.new_profile("group1")
    profile.update_state('EMPTY', stable_min_lim=5, resettable=False)
    profile.update_state(1, stable_min_lim=10, break_trigger=True)
    profile.set_init_states('EMPTY')

    # Профиль можно создать отдельно и добавить позже
    profile = ProfileConfigBuilder("group2")
    profile.update_state('EMPTY', stable_min_lim=15, resettable=False)
    profile.update_state('FULL', stable_min_lim=20)
    profile.set_def_states(['NO_LIBRA', 'EMPTY'])
    builder.add_profile(profile)

    builder.set_profile_ids_map({
        "group1": [101, 102, 103],
        "group2": [201, 202],
    })
    return builder


def cycle(empty: int, full: int, noise: tuple[int, ...] = ()) -> list[int]:
    """ Один цикл EMPTY → FULL → EMPTY заданной длины с шумом в середине FULL. """
    half = full // 2
    return [0] * empty + [1] * half + list(noise) + [1] * (full - half) + [0] * empty


# (pid продукции, последовательность cls_id, ожидаемый профиль, ожидаемое число завершённых циклов)
TEST_CASES: list[tuple[int | None, list[int], str, int]] = [
    (None, cycle(25, 50), "default", 1),
    (None, cycle(25, 50, noise=(3, 3, 3)), "default", 1),
    (None, cycle(25, 40), "default", 0),                 # FULL не достиг порога
    (102, cycle(5, 10) + cycle(5, 10), "group1", 2),
    (102, cycle(5, 10, noise=(3, 0, 3)), "group1", 1),
    (202, cycle(15, 20), "group2", 1),
    (999, cycle(25, 50), "default", 1),                  # неизвестный id → профиль по умолчанию
]
