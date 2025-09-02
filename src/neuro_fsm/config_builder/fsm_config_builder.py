from __future__ import annotations

__all__ = ['FsmConfigBuilder', "ProfileRef"]

from ..validation import ConfigValidator

"""
    Верхне уровневый строитель конфигурации FSM.
    ВАЖНО:
    - Глобальных состояний больше нет. Все состояния и последовательности
      задаются внутри профилей (ProfileConfig). Этот класс НЕ строит профили.
    - Задача этого билдера — собрать верхние параметры (enable, стратегия
      переключателя, default_profile, profile_ids_map, конфиги писателей
      истории) и набор уже готовых профилей (ProfileConfig), после чего
      выпустить неизменяемый FsmConfig.
    - Менеджер сможет инициализироваться тремя способами (будет реализовано в
      менеджере, не здесь):
        1) получить готовый FsmConfigBuilder;
        2) взять последний/по имени из памяти менеджера (без registry в билдере);
        3) распарсить файл (старый путь) и затем прокинуть сюда готовые ProfileConfig.
    Ошибки — на английском, докстринги — на русском.
"""

from typing import Iterable, Optional, Sequence, Union, Mapping, Any, Literal

from ..configs import FsmConfig, ProfileConfig, StateConfig, HistoryWriterConfig
from ..models import ProfileSwitcherStrategies, ProfileNames
from ..utils.type_normalizer import TypeNormalizer


ProfileRef = Union[str, ProfileNames, ProfileConfig]

StateMode = Literal["equal", "individual"]


class FsmConfigBuilder:
    """
        Пошаговый строитель верхне уровневой конфигурации FSM.
        Применение:
            b = FsmConfigBuilder()
            b.set_enable(True)
            b.set_switcher(ProfileSwitcherStrategies.BY_MAPPED_ID)
            b.set_default_profile(ProfileNames.DEFAULT)
            b.set_profile_ids_map({"group1": [101, 102], ProfileNames.DEFAULT: []})
            b.set_raw_history_writer(enable=True, name="{timestamp}_raw.txt", max_age_days=14, async_mode=False)
            b.set_stable_history_writer(enable=True, name="{timestamp}_stable.yaml",
                                        fields=("timestamp","active_profile","state","resetter","breaker","stable","stage_done"),
                                        max_age_days=14, async_mode=False)
            b.add_profile(profile_cfg)  # profile_cfg: ProfileConfig (содержит states/seq/init/default)
            cfg = b.build()
        Замечания:
            - Сеттеры возвращают None (никакого fluent API — явность важнее).
            - Валидация строгая: как минимум один профиль, default_profile должен
              существовать, а cls_id одного и того же состояния не должны
              конфликтовать по полям между профилями.
    """

    __slots__ = (
        "_enable",
        "_states_mode",
        "_switcher_strategy",
        "_default_profile",
        "_profiles",
        "_raw_history_writer",
        "_stable_history_writer",
        "_meta",
    )

    def __init__(self) -> None:
        self._enable: bool = True
        self._states_mode: StateMode = "equal"
        self._switcher_strategy: Optional[ProfileSwitcherStrategies] = ProfileSwitcherStrategies.SINGLE
        self._default_profile: Optional[str] = None
        self._profiles: dict[str, ProfileConfig] = {}
        self._raw_history_writer: Optional[HistoryWriterConfig] = None
        self._stable_history_writer: Optional[HistoryWriterConfig] = None
        self._meta: dict[str, Any] = {}

    def set_enable(self, value: bool = True) -> None:
        """ Включить/выключить FSM. """
        self._enable = bool(value)

    def set_states_mode(self, mode: StateMode) -> None:
        """
            Режим схемы состояний:
              - "equal": во всех профилях один и тот же набор cls_id и имён.
              - "individual": профили могут отличаться по составу состояний.
        """
        self._states_mode = mode

    def set_switcher(self, strategy: Optional[ProfileSwitcherStrategies] = None) -> None:
        """ Установить стратегию переключателя профилей."""
        self._switcher_strategy = strategy if strategy is not None else ProfileSwitcherStrategies.SINGLE

    def add_profile(self, profile: ProfileConfig) -> None:
        """
            Добавляет уже готовый профиль. Профили строятся отдельно
            (ProfileConfigBuilder — отдельный модуль), чтобы избежать смешивания
            ответственности.
        """
        if profile.name in self._profiles:
            raise ValueError(f"Profile {profile.name!r} already exists.")
        self._profiles[profile.name] = profile

    def set_profiles(self, profiles: Iterable[ProfileConfig]) -> None:
        """ Заменяет весь набор профилей (поверх add_profile). """
        self._profiles.clear()
        for profile in profiles:
            self.add_profile(profile)

    def set_default_profile(self, profile: ProfileRef) -> None:
        """ Имя дефолтного профиля или ссылка на него. Должен был быть добавлен до этого в профайлы. """
        if not self._profiles:
            raise ValueError("Profiles are not set yet. Add profiles before calling set_default_profile().")

        name = TypeNormalizer.normalize_to_str_name(profile, case="lower")
        if name not in self._profiles:
            raise ValueError(
                f"Profile '{name}' is not present among added profiles. "
                "Add profile before calling set_default_profile()."
            )

        self._default_profile = name

    def set_profile_ids_map(self, mapping: dict[ProfileRef, Iterable[Union[int, str]]]) -> None:
        """
            Задаёт соответствие <профиль> → <кортеж внешних id>, записывая id внутрь профилей.
            Требует, чтобы профили были уже добавлены (add_profile / set_profiles).
            Args:
                mapping: ключ — str | Enum | объект с .name: str; значение — итерируемые id (int или str).
            Raises:
                ValueError: если профили ещё не заданы; профиль не найден; id не приводятся к int.
        """
        if not self._profiles:
            raise ValueError("Profiles are not set yet. Add profiles before calling set_profile_ids_map().")

        for ref, ids in mapping.items():
            name = TypeNormalizer.normalize_to_str_name(ref, case="lower")
            if name not in self._profiles:
                raise ValueError(
                    f"Profile '{name}' is not present among added profiles. "
                    "Add profile before calling set_profile_ids_map()."
                )

            try:
                ids_tuple: tuple[int, ...] = tuple(int(x) for x in ids)
            except Exception as e:
                raise ValueError(f"Invalid ids for profile '{name}': {e}") from e

            self._profiles[name].set_ids(ids_tuple)

    def set_raw_history_writer(
            self,
            enable: bool,
            name: str,
            max_age_days: int,
            async_mode: bool,
            fields: Sequence[str],
    ) -> None:
        "" "Конфиг для RawHistoryWriter. """
        self._raw_history_writer = HistoryWriterConfig(
            enable=bool(enable),
            name=str(name),
            max_age_days=int(max_age_days),
            async_mode=bool(async_mode),
            fields=tuple(fields),
        )

    def set_stable_history_writer(
            self,
            enable: bool,
            name: str,
            max_age_days: int,
            async_mode: bool,
            fields: Sequence[str],
    ) -> None:
        """Конфиг для StableHistoryWriter."""
        self._stable_history_writer = HistoryWriterConfig(
            enable=bool(enable),
            name=str(name),
            max_age_days=int(max_age_days),
            async_mode=bool(async_mode),
            fields=tuple(fields),
        )

    def set_meta(self, meta: Mapping[str, Any]) -> None:
        """ Полностью заменить meta (поверх существующего). """
        self._meta = dict(meta)

    def update_meta(self, **kwargs: Any) -> None:
        """ Точечное обновление meta. """
        # если _meta ещё не создавалась
        if not hasattr(self, "_meta") or self._meta is None:
            self._meta = {}
        self._meta.update(kwargs)

    def build(self) -> FsmConfig:
        # Финальная архитектурная валидация
        ConfigValidator.run(self._profiles, self._default_profile, self._switcher_strategy)

        # объединённая карта состояний
        union_states: dict[int, StateConfig] = {}
        for prof in self._profiles.values():
            union_states.update(prof.states)

        profiles_tuple = tuple(self._profiles[name] for name in sorted(self._profiles.keys()))

        return FsmConfig(
            enable=self._enable,
            state_configs=union_states,
            profiles=profiles_tuple,
            switcher_strategy=self._switcher_strategy,
            def_profile=self._default_profile,
            profile_ids_map=None,  # ты перенёс хранение id внутрь профилей
            meta=meta,  # ← прокидываем флаг через meta
            raw_history_writer=self._raw_history_writer,
            stable_history_writer=self._stable_history_writer,
        )
