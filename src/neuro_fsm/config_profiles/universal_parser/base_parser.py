__all__ = ['BaseConfigParser']

from abc import ABC, abstractmethod
from typing import Optional

from ..state_machine_config import StateMachineConfig


class BaseConfigParser(ABC):

    @abstractmethod
    def parse(self) -> Optional[StateMachineConfig]:
        """ Основной метод парсинга. Обязательно реализуется в наследниках. """
        ...

    @abstractmethod
    def _validate_required_fields(self) -> None:
        ...

    @abstractmethod
    def _validate_field_types(self) -> None:
        ...
