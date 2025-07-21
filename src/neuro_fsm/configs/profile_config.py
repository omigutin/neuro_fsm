from __future__ import annotations

__all__ = ['ProfileConfig', 'ProfileConfigTuple']

from dataclasses import dataclass
from typing import TypeAlias

from ..core.profiles import ProfileNames
from .state_config import StateConfig, StateConfigDict, StateConfigTuple, StateConfigTupleTuple, StateConfigOrIdType


@dataclass(frozen=True, slots=True)
class ProfileConfig:
    """
        Конфигурация одного статус-профиля машины состояний.
        Содержит:
        - имя профиля;
        - состояния (states) по cls_id;
        - последовательность стартовых состояний (init_states);
        - последовательность состояний по умолчанию (default_states);
        - ожидаемые последовательности состояний (expected_sequences);
        - дополнительное текстовое описание.
        Используется для настройки логики переключения состояний и профилей
        в StateMachine. Позволяет получать конфигурацию конкретного состояния
        по объекту State или по cls_id.
        Immutable: экземпляры нельзя изменять после создания.
    """

    name: ProfileNames
    states: StateConfigDict
    init_states: StateConfigTuple
    default_states: StateConfigTuple
    expected_sequences: StateConfigTupleTuple
    description: str = ""

    def get_state(self, state_or_id: StateConfigOrIdType) -> StateConfig:
        """
            Возвращает конфигурацию состояния по объекту State или cls_id.
            Вызывает ошибку, если конфигурация не найдена.
            Args:
                state_or_id (StateConfigOrIdType): объект состояния или его cls_id.
            Returns:
                State: Состояние.
            Raises:
                ValueError: если конфигурация не найдена.
        """
        cls_id = state_or_id.cls_id if isinstance(state_or_id, StateConfig) else state_or_id
        state = self.states.get(cls_id)
        if state is None:
            raise ValueError(f"Configuration not found for cls_id={cls_id}")
        return state

    def __str__(self):
        return f"StatesProfileConfig(name={self.name})"

ProfileConfigTuple: TypeAlias = tuple[ProfileConfig, ...]
