__all__ = ['BaseConfigParser']

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, ClassVar, Mapping, Optional

from ..config_builder import FsmConfigBuilder
from ..configs import FsmConfig, ProfileConfig, StateConfig
from ..configs.state_config import StateConfigTuple, StateConfigTupleTuple
from ..utils.type_normalizer import TypeNormalizer
from .config_keys import ConfigKeys
from .parsing_utils import parse_bool


class BaseConfigParser(ABC):
    """
        Базовый парсер конфигурации в формате dict (ключи уже приведены к верхнему регистру).
        Парсеры собирают полностью разрешённые ProfileConfig и передают их в FsmConfigBuilder,
        поэтому все форматы проходят одну и ту же проверку.
    """

    FIELD_TYPES: ClassVar[dict[str, tuple[type, ...]]] = {}
    REQUIRED_FIELDS: ClassVar[tuple[str, ...]] = ()

    def __init__(self, config: dict[str, Any]) -> None:
        self._config: dict[str, Any] = config
        self._validate()

    @abstractmethod
    def parse(self) -> FsmConfig:
        """ Возвращает итоговую конфигурацию. """

    # ---------------- общие шаги ----------------

    def _create_builder(self) -> FsmConfigBuilder:
        """ Билдер с общими параметрами: enable, стратегия, писатели истории, meta. """
        builder = FsmConfigBuilder()
        builder.set_states_mode("individual")
        builder.set_enable(parse_bool(self._config.get(ConfigKeys.ENABLE), default=True))
        builder.set_switcher(self._config.get(ConfigKeys.PROFILE_SWITCHER_STRATEGY))
        for key, setter in ((ConfigKeys.RAW_HISTORY_WRITER, builder.set_raw_history_writer),
                            (ConfigKeys.STABLE_HISTORY_WRITER, builder.set_stable_history_writer)):
            writer_cfg = self._config.get(key)
            if writer_cfg is not None:
                setter(**self._parse_history_writer(key, writer_cfg))
        builder.set_meta(self._extract_meta())
        return builder

    def _validate(self) -> None:
        missing = [field for field in self.REQUIRED_FIELDS if field not in self._config]
        if missing:
            raise ValueError(f"[{self.__class__.__name__}] Missing required fields: {', '.join(missing)}")
        for key, expected_types in self.FIELD_TYPES.items():
            if key in self._config and not isinstance(self._config[key], expected_types):
                raise TypeError(
                    f"[{self.__class__.__name__}] Field '{key}' must be of type {expected_types}, "
                    f"got {type(self._config[key])!r}"
                )

    def _extract_meta(self) -> dict[str, Any]:
        """ Нераспознанные ключи конфигурации (в нижнем регистре). """
        return {k.lower(): v for k, v in self._config.items() if k not in ConfigKeys.ALL}

    # ---------------- разбор частей ----------------

    @staticmethod
    def _parse_history_writer(key: str, data: Any) -> dict[str, Any]:
        """ Приводит словарь настроек писателя к аргументам FsmConfigBuilder.set_*_history_writer. """
        if not isinstance(data, Mapping):
            raise TypeError(f"Field '{key}' must be a dict, got {type(data)!r}")
        allowed = {"enable", "name", "max_age_days", "async_mode", "fields"}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"Field '{key}' has unknown keys: {sorted(unknown)}")
        return {
            "enable": parse_bool(data.get("enable"), default=False),
            "name": data.get("name", ""),
            "max_age_days": int(data.get("max_age_days", 14)),
            "async_mode": parse_bool(data.get("async_mode"), default=False),
            "fields": tuple(data.get("fields", ())),
        }

    @staticmethod
    def _get_states_field(data: Mapping[str, Any], plural: str, singular: str) -> Any:
        """ Значение поля, заданного во множественном (INIT_STATES) или единственном (INIT_STATE) числе. """
        if plural in data and singular in data:
            raise ValueError(f"Fields '{plural}' and '{singular}' are mutually exclusive")
        return data.get(plural, data.get(singular))

    @staticmethod
    def _is_single_ref(value: Any) -> bool:
        """ True, если значение — ссылка на одно состояние, а не коллекция ссылок. """
        return not isinstance(value, (list, tuple, set, frozenset))

    @classmethod
    def _resolve_states(cls, profile: ProfileConfig, value: Any, field: str) -> StateConfigTuple:
        """ Разрешает одну ссылку или список ссылок на состояния профиля. None — пусто. """
        if value is None:
            return ()
        refs = (value,) if cls._is_single_ref(value) else tuple(value)
        return tuple(cls._resolve_state(profile, ref, field) for ref in refs)

    @classmethod
    def _resolve_sequences(cls, profile: ProfileConfig, value: Any) -> StateConfigTupleTuple:
        """ Разрешает ожидаемые последовательности. Плоский список трактуется как одна последовательность. """
        if value is None:
            return ()
        if cls._is_single_ref(value):
            raise TypeError(f"Field '{ConfigKeys.EXPECTED_SEQUENCES}' must be a list of sequences, got {value!r}")
        seqs = tuple(value)
        if seqs and all(cls._is_single_ref(item) for item in seqs):
            seqs = (seqs,)
        return tuple(cls._resolve_states(profile, seq, ConfigKeys.EXPECTED_SEQUENCES) for seq in seqs)

    @staticmethod
    def _resolve_state(profile: ProfileConfig, ref: Any, field: str) -> StateConfig:
        """
            Разрешает ссылку на состояние: cls_id, имя, Enum (по имени), StateConfig или объект с name.
            Состояния, заданные через Enum/объект, ищутся по имени, т.к. cls_id в перечислениях классов
            может не совпадать с cls_id модели.
        """
        try:
            if isinstance(ref, (int, str, Enum, StateConfig)):
                return profile.get_state(ref)
            if hasattr(ref, "name"):
                return profile.get_state(ref.name)
        except ValueError as exc:
            raise ValueError(f"Field '{field}': unknown state {ref!r} in profile '{profile.name}'") from exc
        raise TypeError(f"Field '{field}': unsupported state reference {ref!r}")

    @staticmethod
    def _profile_name(raw_name: Optional[Any]) -> str:
        if raw_name is None:
            raise ValueError(f"Profile must have '{ConfigKeys.PROFILE_NAME}'")
        if isinstance(raw_name, Enum):
            return TypeNormalizer.normalize_to_str_name(raw_name, case="lower")
        return str(raw_name)
