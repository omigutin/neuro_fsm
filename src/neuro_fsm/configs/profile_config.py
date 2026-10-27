from __future__ import annotations

__all__ = ['ProfileConfig', 'ProfileConfigTuple']

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Iterable, TypeAlias, Union

from ..utils.type_normalizer import TypeNormalizer
from .state_config import StateConfig, StateConfigOrIdType, StateConfigDict, StateConfigTuple, StateConfigTupleTuple


@dataclass(slots=True)
class ProfileConfig:
    """
        Полностью разрешённая конфигурация одного профиля машины состояний.
        Модель изменяема на этапе сборки (билдером или парсером); после FsmConfigBuilder.build()
        считается зафиксированной.
        Поля:
            name: имя профиля (приводится к нижнему регистру);
            states: карта cls_id -> StateConfig;
            init_states: стартовые состояния (последнее — текущее состояние при старте);
            default_states: состояния по умолчанию (последнее используется для неизвестного cls_id);
            expected_sequences: ожидаемые последовательности стабильных состояний;
            mapped_ids: внешние id (например, id продукции) для стратегии BY_MAPPED_ID;
            description: произвольное описание.
    """

    name: str
    states: StateConfigDict = field(default_factory=dict)
    init_states: StateConfigTuple = field(default_factory=tuple)
    default_states: StateConfigTuple = field(default_factory=tuple)
    expected_sequences: StateConfigTupleTuple = field(default_factory=tuple)
    mapped_ids: tuple[int, ...] = field(default_factory=tuple)
    description: str = ""

    def __post_init__(self) -> None:
        """ Нормализует имя профиля (str | Enum) к строке в нижнем регистре. """
        self.name = TypeNormalizer.normalize_to_str_name(self.name, case="lower")
        if not self.name:
            raise ValueError("[ProfileConfig] name must not be empty")

    # ---------------- состояния ----------------

    def new_state(self, *, cls_id: int, name: str, **attrs: Any) -> StateConfig:
        """ Добавляет новое состояние. Имя и cls_id должны быть уникальны в профиле. """
        if cls_id in self.states:
            raise ValueError(f"State cls_id={cls_id} already exists in profile '{self.name}'.")
        if self.find_state_by_name(name) is not None:
            raise ValueError(f"State name '{name}' already exists in profile '{self.name}'.")
        state = StateConfig(cls_id=cls_id, name=name, **attrs)
        self.states[state.cls_id] = state
        return state

    def update_state(self, ref: Union[StateConfigOrIdType, str, Enum], **patch: Any) -> StateConfig:
        """ Изменяет параметры существующего состояния (без смены cls_id и name). """
        current = self.get_state(ref)
        if "name" in patch and patch["name"] != current.name:
            raise ValueError("update_state: changing 'name' is not allowed.")
        if "cls_id" in patch and patch["cls_id"] != current.cls_id:
            raise ValueError("update_state: changing 'cls_id' is not allowed.")
        updated = replace(current, **patch)
        self.states[current.cls_id] = updated
        # Ссылки в init/default/sequences должны указывать на актуальные объекты
        self._relink_state(updated)
        return updated

    def get_state(self, ref: Union[StateConfigOrIdType, str, Enum]) -> StateConfig:
        """ Возвращает состояние по cls_id, имени, Enum (по имени) или StateConfig (по cls_id). """
        if isinstance(ref, StateConfig):
            state = self.states.get(ref.cls_id)
        elif isinstance(ref, bool):
            state = None
        elif isinstance(ref, int):
            state = self.states.get(ref)
        else:
            state = self.find_state_by_name(TypeNormalizer.normalize_state_ref_name(ref))
        if state is None:
            raise ValueError(f"State {ref!r} not found in profile '{self.name}'.")
        return state

    def find_state_by_name(self, name: str) -> StateConfig | None:
        """ Ищет состояние по имени. """
        return next((s for s in self.states.values() if s.name == name), None)

    # ---------------- init/default/sequences ----------------

    def set_init_states(self, states: Iterable[StateConfig]) -> None:
        """ Полностью перезаписывает стартовые состояния. """
        self.init_states = tuple(states)

    def set_default_states(self, states: Iterable[StateConfig]) -> None:
        """ Полностью перезаписывает состояния по умолчанию. """
        self.default_states = tuple(states)

    def add_expected_sequence(self, seq: Iterable[StateConfig]) -> None:
        """ Добавляет одну ожидаемую последовательность. """
        self.expected_sequences = (*self.expected_sequences, tuple(seq))

    def set_expected_sequences(self, seqs: Iterable[Iterable[StateConfig]]) -> None:
        """ Полностью перезаписывает набор ожидаемых последовательностей. """
        self.expected_sequences = tuple(tuple(seq) for seq in seqs)

    # ---------------- внешние id ----------------

    def set_ids(self, ids: Iterable[int]) -> None:
        """ Присваивает профилю внешний список id. """
        self.mapped_ids = tuple(int(x) for x in ids)

    def get_ids(self) -> tuple[int, ...]:
        """ Возвращает внешние id профиля. """
        return self.mapped_ids

    # ---------------- служебное ----------------

    def to_dict(self) -> dict[str, Any]:
        """ Сериализует профиль в словарь (состояния в последовательностях — по именам). """
        return {
            'name': self.name,
            'states': {k: state.to_dict() for k, state in self.states.items()},
            'init_states': [state.name for state in self.init_states],
            'default_states': [state.name for state in self.default_states],
            'expected_sequences': [[state.name for state in seq] for seq in self.expected_sequences],
            'mapped_ids': list(self.mapped_ids),
            'description': self.description,
        }

    def _relink_state(self, state: StateConfig) -> None:
        """ Заменяет в init/default/sequences старую версию состояния на новую. """
        def relink(items: StateConfigTuple) -> StateConfigTuple:
            return tuple(state if s.cls_id == state.cls_id else s for s in items)

        self.init_states = relink(self.init_states)
        self.default_states = relink(self.default_states)
        self.expected_sequences = tuple(relink(seq) for seq in self.expected_sequences)

    def __str__(self) -> str:
        return f"ProfileConfig(name={self.name})"


ProfileConfigTuple: TypeAlias = tuple[ProfileConfig, ...]
