__all__ = ['StateParser']

from typing import Any, Sequence, Union
from enum import Enum

from ...models import State, StateMeta, StateParams, StatesDict, StatesTupleTuple, StatesTuple


class StateParser:
    """
        Универсальный парсер состояний из конфигураций.
        Поддерживает форматы: JSON/YAML словари, Enum, вложенные структуры профилей.
    """

    @staticmethod
    def build_states_dict(raw: Sequence[Any]) -> StatesDict:
        """
            Массовая загрузка состояний из списка словарей (или экземпляров Enum/State).
            Args:
                raw (list[dict | Enum | State]): Список элементов для парсинга.
            Returns:
                dict[int, State]: Словарь cls_id → State.
        """
        states: list[State] = []
        for item in raw:
            if isinstance(item, State):
                states.append(item)
            elif isinstance(item, dict):
                states.append(StateParser._from_dict(item))
            elif isinstance(item, Enum):
                states.append(StateParser._from_enum(item))
            elif hasattr(item, "cls_id") and hasattr(item, "name"):
                # Поддержка нестандартных объектов с нужными атрибутами
                states.append(StateParser._from_enum(item))
            else:
                raise TypeError(f"Unsupported state config type: {type(item)}")
        return {s.cls_id: s for s in states}

    @staticmethod
    def override_states(base: StatesDict, overrides: Sequence[dict[str, Any]]) -> StatesDict:
        """
            Переопределяет параметры состояний, не изменяя cls_id и name.
            Поддерживает как "плоские", так и вложенные ('params') форматы конфигураций.
            Args:
                base (StatesDict): Базовые состояния (cls_id → State).
                overrides (list[dict]): Переопределения (по 'cls_id' или 'name').
            Returns:
                StatesDict: Новый словарь cls_id → State с учётом переопределений.
        """
        result = {}
        for cls_id, state in base.items():
            result[cls_id] = State(
                meta=state.meta,
                params=StateParams(
                    stable_min_lim=state.params.stable_min_lim,
                    resettable=state.params.resettable,
                    reset_trigger=state.params.reset_trigger,
                    break_trigger=state.params.break_trigger,
                    threshold=state.params.threshold,
                ),
            )

        for override in overrides:
            key = override.get("cls_id") or override.get("name")
            match: State | None = None

            # Поиск соответствия
            if isinstance(key, int):
                match = base.get(key)
                if match and "name" in override and override["name"] != match.name:
                    raise ValueError(
                        f"[StateParser] Override mismatch: cls_id={key} ≠ name='{override['name']}' (expected '{match.name}')")
            elif isinstance(key, str):
                match = next((s for s in base.values() if s.name == key), None)
                if match and "cls_id" in override and override["cls_id"] != match.cls_id:
                    raise ValueError(
                        f"[StateParser] Override mismatch: name={key} ≠ cls_id={override['cls_id']} (expected {match.cls_id})")

            if not match:
                raise ValueError(f"[StateParser] Override target not found for key={key}")

            # Извлечение параметров — поддержка вложенного и плоского формата
            params_raw = override["params"] if "params" in override else override

            result[match.cls_id] = State(
                meta=match.meta,
                params=StateParams(
                    stable_min_lim=params_raw.get("stable_min_lim", match.params.stable_min_lim),
                    resettable=params_raw.get("resettable", match.params.resettable),
                    reset_trigger=params_raw.get("reset_trigger", match.params.reset_trigger),
                    break_trigger=params_raw.get("break_trigger", match.params.break_trigger),
                    threshold=params_raw.get("threshold", match.params.threshold),
                )
            )

        return result

    @staticmethod
    def resolve_state_reference(ref: str | int, states: StatesDict) -> State:
        """
            Разрешает ссылку на состояние: по int (cls_id), str (name), Enum, или самому State.
            Args:
                ref: ссылка на состояние.
                states: словарь всех известных состояний.
            Returns:
                State: соответствующее состояние.
        """
        if isinstance(ref, State):
            return ref
        elif isinstance(ref, int):
            return states[ref]
        elif isinstance(ref, str):
            for state in states.values():
                if state.name == ref:
                    return state
            raise ValueError(f"[resolve_state_reference] Unknown state name: {ref}")
        elif isinstance(ref, Enum):
            return StateParser.resolve_state_reference(ref.name, states)
        elif hasattr(ref, "cls_id") and hasattr(ref, "name"):
            return StateParser.resolve_state_reference(ref.name, states)
        raise TypeError(f"Cannot resolve state reference of type {type(ref)}: {ref}")

    @staticmethod
    def resolve_state_list(values: Sequence[str | int], states: StatesDict) -> StatesTuple:
        return tuple(StateParser.resolve_state_reference(v, states) for v in values)

    @staticmethod
    def resolve_state_sequence(values: Sequence[Sequence[str | int]], states: StatesDict) -> StatesTupleTuple:
        return tuple(tuple(StateParser.resolve_state_reference(v, states) for v in seq) for seq in values)

    @staticmethod
    def _from_dict(d: dict[str, Any]) -> State:
        """
            Создание State из словаря верхнего уровня.
            Args:
                d (dict): Словарь с ключами:
                          - 'name', 'cls_id', 'full_name', 'fiction' (для meta)
                          - 'stable_min_lim', 'resettable', 'reset_trigger', 'break_trigger', 'threshold' (для params)
            Returns:
                State: Объект состояния.
        """
        return State(
            meta=StateMeta(
                name=d["name"],
                cls_id=d["cls_id"],
                full_name=d.get("full_name", ""),
                fiction=d.get("fiction", False),
            ),
            params=StateParams(
                stable_min_lim=d.get("stable_min_lim"),
                resettable=d.get("resettable", False),
                reset_trigger=d.get("reset_trigger", False),
                break_trigger=d.get("break_trigger", False),
                threshold=d.get("threshold"),
            ),
        )

    @staticmethod
    def _from_enum(enum_member: Union[Enum, Any]) -> State:
        """
            Преобразует enum-член (с value: NeuroClass) или объект с атрибутами в State.
            Args:
                enum_member (Enum | Any): элемент перечисления или совместимый объект.
            Returns:
                State: экземпляр состояния.
        """
        obj = enum_member.value if isinstance(enum_member, Enum) else enum_member
        return State(
            meta=StateMeta(
                name=obj.name,
                cls_id=obj.cls_id,
                full_name=getattr(obj, "full_name", ""),
                fiction=getattr(obj, "fiction", False),
            ),
            params=StateParams(
                threshold=getattr(obj, "threshold", None)
            )
        )
