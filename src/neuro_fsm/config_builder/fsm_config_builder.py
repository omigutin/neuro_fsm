from __future__ import annotations

__all__ = ["FsmConfigBuilder", "ProfileRef", "StatesMode"]

from enum import Enum
from typing import Any, Iterable, Literal, Mapping, Optional, Sequence, Union

from ..configs import FsmConfig, ProfileConfig, HistoryWriterConfig
from ..models import ProfileSwitcherStrategies, ProfileNames
from ..utils.type_normalizer import TypeNormalizer
from ..validation import ConfigValidator
from .profile_config_builder import ProfileConfigBuilder

ProfileRef = Union[str, ProfileNames, ProfileConfig, ProfileConfigBuilder]
StatesMode = Literal["equal", "individual"]
_ProfileSource = Union[ProfileConfigBuilder, ProfileConfig]


class FsmConfigBuilder:
    """
        Основной способ задания конфигурации FSM.
        Режимы состояний (set_states_mode):
            - "equal" (по умолчанию): состояния объявляются в профиле по умолчанию, остальные профили
              наследуют их и меняют только нужные параметры (update_state). Набор состояний во всех
              профилях одинаков;
            - "individual": каждый профиль объявляет свои состояния самостоятельно.
        Пример:
            b = FsmConfigBuilder()
            b.set_switcher(ProfileSwitcherStrategies.BY_MAPPED_ID)
            base = b.new_profile("default", default=True)
            base.new_state(cls_id=0, name="EMPTY", stable_min_lim=25, resettable=True, reset_trigger=True)
            base.new_state(cls_id=1, name="FULL", stable_min_lim=50, reset_trigger=True)
            base.set_init_states("EMPTY")
            base.set_exp_seqs(("EMPTY", "FULL", "EMPTY"))
            group = b.new_profile("group1")
            group.update_state("EMPTY", stable_min_lim=5)
            b.set_profile_ids_map({"group1": [101, 102]})
            cfg = b.build()
    """

    __slots__ = ("_enable", "_states_mode", "_switcher_strategy", "_default_profile", "_profiles",
                 "_raw_history_writer", "_stable_history_writer", "_meta")

    def __init__(self) -> None:
        self._enable: bool = True
        self._states_mode: StatesMode = "equal"
        self._switcher_strategy: ProfileSwitcherStrategies = ProfileSwitcherStrategies.SINGLE
        self._default_profile: Optional[str] = None
        self._profiles: dict[str, _ProfileSource] = {}
        self._raw_history_writer: HistoryWriterConfig = HistoryWriterConfig.disabled()
        self._stable_history_writer: HistoryWriterConfig = HistoryWriterConfig.disabled()
        self._meta: dict[str, Any] = {}

    # ---------- верхние параметры ----------

    def set_enable(self, value: bool = True) -> None:
        """ Включить/выключить FSM. """
        self._enable = bool(value)

    def set_states_mode(self, mode: StatesMode) -> None:
        """ Режим состояний: "equal" или "individual" (см. описание класса). """
        if mode not in ("equal", "individual"):
            raise ValueError(f"Unknown states mode {mode!r}. Expected 'equal' or 'individual'.")
        self._states_mode = mode

    def set_switcher(self, strategy: Union[ProfileSwitcherStrategies, str, None] = None) -> None:
        """ Устанавливает стратегию переключения профилей (Enum или имя). None — SINGLE. """
        self._switcher_strategy = ProfileSwitcherStrategies.parse(strategy)

    # ---------- профили ----------

    def new_profile(self, name: Union[str, Enum], default: bool = False) -> ProfileConfigBuilder:
        """ Создаёт билдер профиля, регистрирует его и возвращает для дальнейшей настройки. """
        builder = ProfileConfigBuilder(name)
        self.add_profile(builder, default=default)
        return builder

    def add_profile(self, profile: _ProfileSource, default: bool = False) -> None:
        """ Добавляет подготовленный профиль: ProfileConfigBuilder или готовый ProfileConfig. """
        if not isinstance(profile, (ProfileConfigBuilder, ProfileConfig)):
            raise TypeError(f"Unsupported profile type: {type(profile)!r}")
        if profile.name in self._profiles:
            raise ValueError(f"Profile {profile.name!r} already exists.")
        self._profiles[profile.name] = profile
        if default:
            self._default_profile = profile.name

    def set_profiles(self, profiles: Iterable[_ProfileSource]) -> None:
        """ Полностью заменяет набор профилей. Профиль по умолчанию сбрасывается. """
        self._profiles.clear()
        self._default_profile = None
        for profile in profiles:
            self.add_profile(profile)

    def set_default_profile(self, profile: ProfileRef) -> None:
        """ Устанавливает профиль по умолчанию. Профиль должен быть уже добавлен. """
        name = self._ref_to_name(profile)
        if name not in self._profiles:
            raise ValueError(f"Profile '{name}' is not present among added profiles.")
        self._default_profile = name

    def set_profile_ids_map(self, mapping: Mapping[ProfileRef, Optional[Iterable[Union[int, str]]]]) -> None:
        """
            Задаёт внешние id профилей: {профиль: [id, ...]}. Профили должны быть уже добавлены.
            Пустой список или None — у профиля нет id.
        """
        for ref, ids in mapping.items():
            name = self._ref_to_name(ref)
            if name not in self._profiles:
                raise ValueError(f"Profile '{name}' is not present among added profiles.")
            try:
                ids_tuple = tuple(int(x) for x in (ids or ()))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid ids for profile '{name}': {ids!r}") from exc
            self._profiles[name].set_ids(ids_tuple)

    def get_profile(self, name: Union[str, Enum]) -> Optional[_ProfileSource]:
        """ Возвращает профиль (билдер или конфиг) по имени или None. """
        return self._profiles.get(self._ref_to_name(name))

    def remove_profile(self, name: Union[str, Enum]) -> None:
        """ Удаляет профиль. Если он был профилем по умолчанию — сбрасывает выбор. """
        name_norm = self._ref_to_name(name)
        if name_norm not in self._profiles:
            raise KeyError(f"Profile {name_norm!r} not found.")
        del self._profiles[name_norm]
        if self._default_profile == name_norm:
            self._default_profile = None

    def list_profiles(self) -> tuple[str, ...]:
        """ Имена профилей в порядке добавления. """
        return tuple(self._profiles.keys())

    def has_profile(self, name: Union[str, Enum]) -> bool:
        """ True, если профиль добавлен. """
        return self._ref_to_name(name) in self._profiles

    # ---------- писатели истории / meta ----------

    def set_raw_history_writer(
            self,
            enable: bool,
            name: str,
            max_age_days: int = 14,
            async_mode: bool = False,
            fields: Sequence[str] = (),
    ) -> None:
        """ Настройки писателя сырой истории (каждый входной cls_id). """
        self._raw_history_writer = HistoryWriterConfig(
            enable=bool(enable), name=str(name), max_age_days=int(max_age_days),
            async_mode=bool(async_mode), fields=tuple(fields),
        )

    def set_stable_history_writer(
            self,
            enable: bool,
            name: str,
            max_age_days: int = 14,
            async_mode: bool = False,
            fields: Sequence[str] = (),
    ) -> None:
        """ Настройки писателя стабильной истории (события, смены профилей, срабатывания). """
        self._stable_history_writer = HistoryWriterConfig(
            enable=bool(enable), name=str(name), max_age_days=int(max_age_days),
            async_mode=bool(async_mode), fields=tuple(fields),
        )

    def set_meta(self, meta: Mapping[str, Any]) -> None:
        """ Полностью заменяет meta. """
        self._meta = dict(meta)

    def update_meta(self, **kwargs: Any) -> None:
        """ Точечное обновление meta. """
        self._meta.update(kwargs)

    # ---------- финализация ----------

    def build(self) -> FsmConfig:
        """
            Собирает и проверяет конфигурацию:
              1) определяет профиль по умолчанию (если профиль один — он и есть по умолчанию);
              2) собирает профили (в режиме "equal" — с наследованием от профиля по умолчанию);
              3) проверяет конфигурацию (ConfigValidator);
              4) возвращает FsmConfig.
        """
        if not self._profiles:
            raise ValueError("No profiles were added. Add at least one profile before build().")

        def_name = self._resolve_default_profile()
        built: dict[str, ProfileConfig] = {}

        base_source = self._profiles[def_name]
        base = base_source.build() if isinstance(base_source, ProfileConfigBuilder) else base_source
        inherit_from = base if self._states_mode == "equal" else None

        for name, source in self._profiles.items():
            if name == def_name:
                built[name] = base
            elif isinstance(source, ProfileConfigBuilder):
                built[name] = source.build(inherit_from)
            else:
                built[name] = source

        ConfigValidator.run(built, def_name, self._switcher_strategy, self._states_mode)

        return FsmConfig(
            enable=self._enable,
            profiles=tuple(built.values()),
            def_profile=def_name,
            switcher_strategy=self._switcher_strategy,
            meta=self._meta,
            raw_history_writer=self._raw_history_writer,
            stable_history_writer=self._stable_history_writer,
        )

    def _resolve_default_profile(self) -> str:
        """ Возвращает имя профиля по умолчанию. """
        if self._default_profile is not None:
            return self._default_profile
        if len(self._profiles) == 1:
            return next(iter(self._profiles))
        raise ValueError(
            "Default profile is not set. Use new_profile(..., default=True) or set_default_profile()."
        )

    @staticmethod
    def _ref_to_name(ref: Union[ProfileRef, Enum]) -> str:
        """ Приводит ссылку на профиль к нормализованному имени. """
        if isinstance(ref, (ProfileConfig, ProfileConfigBuilder)):
            return ref.name
        return TypeNormalizer.normalize_to_str_name(ref, case="lower")
