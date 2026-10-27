from __future__ import annotations

__all__ = ['ProfileConfigBuilder', 'StateConfigRef']

from enum import Enum
from typing import Any, Iterable, Optional, Union

from ..configs import StateConfig, ProfileConfig
from ..configs.state_config import StateConfigDict, StateConfigTuple
from ..utils.type_normalizer import TypeNormalizer

StateConfigRef = Union[int, str, Enum, StateConfig]


class ProfileConfigBuilder:
    """
        Пошаговый билдер одного профиля.
        Билдер только запоминает операции; ссылки на состояния (cls_id, имя, Enum, StateConfig) разрешаются
        в build(). Это позволяет профилю наследовать состояния базового профиля (режим "equal"
        в FsmConfigBuilder) и задавать вызовы в любом порядке.
        Правила наследования от базового профиля:
            - состояния базового профиля копируются, затем применяются update_state();
            - init/default состояния и ожидаемые последовательности наследуются, если не заданы в профиле;
            - add_exp_seq()/set_exp_seqs() в профиле полностью заменяют унаследованные последовательности.
    """

    __slots__ = ("_name", "_description", "_states", "_patches", "_init_refs", "_def_refs", "_seq_refs", "_ids")

    def __init__(self, name: Union[str, Enum], description: str = "") -> None:
        self._name: str = TypeNormalizer.normalize_to_str_name(name, case="lower")
        if not self._name:
            raise ValueError("[ProfileConfigBuilder] profile name must not be empty")
        self._description: str = description
        self._states: StateConfigDict = {}
        self._patches: list[tuple[StateConfigRef, dict[str, Any]]] = []
        self._init_refs: Optional[tuple[StateConfigRef, ...]] = None
        self._def_refs: Optional[tuple[StateConfigRef, ...]] = None
        self._seq_refs: Optional[tuple[tuple[StateConfigRef, ...], ...]] = None
        self._ids: tuple[int, ...] = ()

    @property
    def name(self) -> str:
        """ Имя профиля (в нижнем регистре). """
        return self._name

    @property
    def declared_states(self) -> StateConfigDict:
        """ Состояния, объявленные непосредственно в этом профиле (без унаследованных). """
        return dict(self._states)

    # ---------------- состояния ----------------

    def new_state(self, *, cls_id: int, name: str, **attrs: Any) -> StateConfig:
        """ Объявляет новое состояние профиля. cls_id и имя должны быть уникальны. """
        if cls_id in self._states:
            raise ValueError(f"State cls_id={cls_id} already declared in profile '{self._name}'.")
        if any(s.name == name for s in self._states.values()):
            raise ValueError(f"State name '{name}' already declared in profile '{self._name}'.")
        state = StateConfig(cls_id=cls_id, name=name, **attrs)
        self._states[state.cls_id] = state
        return state

    def update_state(self, name_or_id: StateConfigRef, **patch: Any) -> None:
        """ Запоминает изменение параметров состояния (своего или унаследованного). """
        if "name" in patch or "cls_id" in patch:
            raise ValueError("update_state: changing 'name' or 'cls_id' is not allowed.")
        if not patch:
            raise ValueError("update_state: nothing to update.")
        self._patches.append((name_or_id, dict(patch)))

    # ---------------- init/default ----------------

    def set_init_states(self, states: Union[StateConfigRef, Iterable[StateConfigRef]]) -> None:
        """ Задаёт стартовые состояния (одно или несколько). Последнее — текущее при старте. """
        self._init_refs = self._normalize_refs(states)

    def set_def_states(self, states: Union[StateConfigRef, Iterable[StateConfigRef]]) -> None:
        """ Задаёт состояния по умолчанию (одно или несколько). Последнее — для неизвестных cls_id. """
        self._def_refs = self._normalize_refs(states)

    # ---------------- ожидаемые последовательности ----------------

    def add_exp_seq(self, seq: Iterable[StateConfigRef]) -> None:
        """ Добавляет одну ожидаемую последовательность. """
        refs = self._normalize_refs(seq)
        if not refs:
            raise ValueError(f"Expected sequence must not be empty (profile '{self._name}').")
        self._seq_refs = (*(self._seq_refs or ()), refs)

    def add_exp_seqs(self, seqs: Iterable[Iterable[StateConfigRef]]) -> None:
        """ Добавляет несколько ожидаемых последовательностей. """
        for seq in seqs:
            self.add_exp_seq(seq)

    def set_exp_seqs(self, seqs: Iterable[Iterable[StateConfigRef]]) -> None:
        """
            Полностью задаёт набор ожидаемых последовательностей.
            Одна последовательность также допустима: set_exp_seqs(('EMPTY', 'FULL', 'EMPTY')).
        """
        items = tuple(seqs)
        self._seq_refs = ()
        if items and all(self._is_single_ref(item) for item in items):
            self.add_exp_seq(items)  # type: ignore[arg-type]
        else:
            self.add_exp_seqs(items)

    # ---------------- внешние id ----------------

    def set_ids(self, ids: Iterable[int]) -> None:
        """ Присваивает профилю внешние id (стратегия BY_MAPPED_ID). """
        self._ids = tuple(int(x) for x in ids)

    def get_ids(self) -> tuple[int, ...]:
        return self._ids

    # ---------------- сборка ----------------

    def build(self, base: Optional[ProfileConfig] = None) -> ProfileConfig:
        """
            Собирает ProfileConfig.
            Args:
                base: базовый профиль для наследования (режим "equal"). None — профиль самостоятельный.
        """
        states: StateConfigDict = dict(base.states) if base else {}
        for cls_id, state in self._states.items():
            if base is not None and cls_id in states:
                raise ValueError(
                    f"State cls_id={cls_id} is inherited from profile '{base.name}' and cannot be redeclared "
                    f"in profile '{self._name}'. Use update_state()."
                )
            states[cls_id] = state

        profile = ProfileConfig(name=self._name, states=states, description=self._description)
        profile.set_ids(self._ids)

        for ref, patch in self._patches:
            profile.update_state(self._resolve(profile, ref), **patch)

        profile.set_init_states(self._resolve_many(profile, self._init_refs, base.init_states if base else ()))
        profile.set_default_states(self._resolve_many(profile, self._def_refs, base.default_states if base else ()))
        if self._seq_refs is not None:
            profile.set_expected_sequences(self._resolve_many(profile, seq, ()) for seq in self._seq_refs)
        elif base is not None:
            profile.set_expected_sequences(self._resolve_many(profile, seq, ()) for seq in base.expected_sequences)
        return profile

    def _resolve_many(
            self,
            profile: ProfileConfig,
            refs: Optional[Iterable[StateConfigRef]],
            inherited: StateConfigTuple
    ) -> StateConfigTuple:
        """ Разрешает ссылки в объекты StateConfig профиля; None — взять унаследованные. """
        source = inherited if refs is None else refs
        return tuple(self._resolve(profile, ref) for ref in source)

    def _resolve(self, profile: ProfileConfig, ref: StateConfigRef) -> StateConfig:
        """ Разрешает одну ссылку на состояние с понятной ошибкой. """
        try:
            return profile.get_state(ref)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Unknown state {ref!r} in profile '{self._name}'.") from exc

    @classmethod
    def _normalize_refs(cls, value: Union[StateConfigRef, Iterable[StateConfigRef]]) -> tuple[StateConfigRef, ...]:
        """ Приводит одиночную ссылку или последовательность ссылок к кортежу. """
        if cls._is_single_ref(value):
            return (value,)  # type: ignore[return-value]
        refs = tuple(value)  # type: ignore[arg-type]
        for ref in refs:
            if not cls._is_single_ref(ref):
                raise TypeError(f"Unsupported state reference: {ref!r}")
        return refs

    @staticmethod
    def _is_single_ref(value: Any) -> bool:
        """ True, если значение — ссылка на одно состояние. """
        return isinstance(value, (int, str, Enum, StateConfig)) and not isinstance(value, bool)

    def __repr__(self) -> str:
        return f"<ProfileConfigBuilder {self._name}>"
