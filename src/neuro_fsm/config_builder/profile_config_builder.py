from __future__ import annotations

__all__ = ['ProfileConfigBuilder']

from dataclasses import replace
from typing import Iterable, Sequence, Union

from ..configs import StateConfig, ProfileConfig  # предполагаем твои dataclass'ы с .states: dict[int, StateConfig]
from ..configs.state_config import StateConfigDict, StateConfigTuple, StateConfigTupleTuple

StateConfigRef = Union[int, str, StateConfig]


class ProfileConfigBuilder:
    """
        Локальный билдер профиля.
        Правила нейминга:
          - set_*  — создаёт новое или устанавливает значение целиком (может зачистить то, что было до этого).
          - override_* — перезаписывает существующее (ошибка, если нечего перезаписывать).
        Порядок вызовов может быть любой: ссылки на состояния (по имени/ID/StateConfig) можно передавать
        до их явного объявления — они будут разрешены позже на этапе финализации FsmConfigBuilder (орchestrator).
        Внутри этого билдера мы стараемся разрешать ссылки сразу, если это возможно.
    """

    __slots__ = (
        "_name",
        "_states",
        "_name_to_id",  # dict[name, cls_id] (уникальные name внутри профиля)
        "_init_states",  # tuple[StateConfigRef, ...]  (пока «сырые» ссылки, разрешим позже)
        "_def_states",  # tuple[StateConfigRef, ...]
        "_expected_states",  # tuple[tuple[StateConfigRef, ...], ...]
        "_ids",  # tuple[int, ...]  (если задаёшь внешние id профиль->ids где-то тут)
        "_default"  # bool-маркер кандидата на default (используется сверху)
    )

    def __init__(self, name: str, default: bool= False) -> None:
        self._name: str = name
        self._states: StateConfigDict = {}
        self._name_to_id: dict[str, int] = {}
        self._init_states: StateConfigTuple = tuple()
        self._def_states: StateConfigTuple = tuple()
        self._expected_states: StateConfigTupleTuple = tuple()
        self._ids: tuple[int, ...] = tuple()
        self._default: bool = bool(default)

    def set_state(self, *, cls_id: int, name: str, **attrs) -> StateConfig:
        """
            Создаёт/устанавливает состояние (по cls_id) с указанным именем и атрибутами.
            Если состояние с таким cls_id уже есть — полностью заменяется.
            Имя должно быть уникальным внутри профиля.
            Returns:
                StateConfig — ссылка на состояние; её можно передавать как StateConfigRef.
        """
        # Проверка уникальности name (если имя уже занято другим cls_id)
        other_state_id = self._name_to_id.get(name)
        if other_state_id is not None and other_state_id != cls_id:
            raise ValueError(
                f"State name '{name}' already bound to cls_id={other_state_id} in profile '{self._name}'. "
                f"Names must be unique within a profile."
            )

        sc = StateConfig(cls_id=cls_id, name=name, **attrs)

        # Если имя было привязано к этому же cls_id или не было вовсе — нормализуем мэп
        self._name_to_id[name] = cls_id
        self._states[cls_id] = sc
        return sc  # ссылка

    def override_state(self, *, name_or_id: StateConfigRef, **patch) -> None:
        """
        Перезаписывает (патчит) уже существующее состояние.
        Ошибка, если состояние не найдено.
        """
        cls_id = self._resolve_to_id_strict(name_or_id)
        if cls_id not in self._states:
            raise ValueError(
                f"Cannot override state: cls_id={cls_id} not found in profile '{self._name}'."
            )
        current = self._states[cls_id]

        # запрещаем менять имя через override — иначе нарушится уникальность/карта имён
        if "name" in patch and patch["name"] != current.name:
            raise ValueError(
                f"override_state: changing 'name' is not allowed (was {current.name!r}, new {patch['name']!r}). "
                "Use set_state to (re)define the state."
            )
        # также запрещаем менять cls_id
        if "cls_id" in patch and patch["cls_id"] != current.cls_id:
            raise ValueError(
                f"override_state: changing 'cls_id' is not allowed. "
                "Use set_state to (re)define the state with another id."
            )

        self._states[cls_id] = replace(current, **patch)

    # ---------------- init/def ----------------

    def set_init_states(self, states: StateConfigRef | Iterable[StateConfigRef]) -> None:
        """Устанавливает стартовые состояния (заменяет полностью). Принимает ссылку или последовательность ссылок."""
        self._init_states = self._normalize_refs_input(states)

    def override_init_states(self, states: StateConfigRef | Iterable[StateConfigRef]) -> None:
        """Перезаписывает стартовые состояния (ошибка, если ранее не задавались? — нет, просто заменяем)."""
        if not self._init_states:
            # По твоей политике override «перезаписывает», но не будем строго требовать наличия — просто заменим.
            pass
        self._init_states = self._normalize_refs_input(states)

    def set_def_states(self, states: StateConfigRef | Iterable[StateConfigRef]) -> None:
        """Устанавливает дефолтные состояния (заменяет полностью)."""
        self._def_states = self._normalize_refs_input(states)

    def override_def_states(self, states: StateConfigRef | Iterable[StateConfigRef]) -> None:
        """Перезаписывает дефолтные состояния (аналогично override_init_states)."""
        if not self._def_states:
            pass
        self._def_states = self._normalize_refs_input(states)

    # ---------------- ожидаемые последовательности ----------------

    def set_expected_sequences(self, seqs: Iterable[Sequence[StateConfigRef]]) -> None:
        """
        Устанавливает ожидаемые последовательности (заменяет полностью).
        Принимает iterable последовательностей ссылок на состояния.
        """
        self._expected_states = tuple(tuple(seq) for seq in seqs)

    def set_expected_sequence(
        self,
        seq_or_seqs: Sequence[StateConfigRef] | Iterable[Sequence[StateConfigRef]],
    ) -> None:
        """
        Устанавливает ожидаемые последовательности (заменяет полностью).
        Может принять:
          - одну последовательность ссылок, или
          - итерируемый набор последовательностей ссылок.
        """
        if not seq_or_seqs:
            self._expected_states = tuple()
            return

        # различаем «одну последовательность» и «много последовательностей»
        if isinstance(seq_or_seqs, (list, tuple)) and seq_or_seqs and not _is_sequence_of_sequences(seq_or_seqs):
            self._expected_states = (tuple(seq_or_seqs),)
        else:
            self._expected_states = tuple(tuple(s) for s in seq_or_seqs)  #
