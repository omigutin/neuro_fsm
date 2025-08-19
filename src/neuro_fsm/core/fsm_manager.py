from __future__ import annotations

__all__ = ['FsmManager']

from typing import Optional, Any, TYPE_CHECKING

from ..models import ProfileNames
from .fsm import Fsm

if TYPE_CHECKING:
    from ..configs.state_config import StateConfigDict


class FsmManager:
    """
        Менеджер конфигураций для машин состояний.
        Отвечает за:
        - загрузку и парсинг конфигурации;
        - создание экземпляров StateMachine с актуальной конфигурацией.
    """

    def __init__(self, raw_config: Optional[Any] = None) -> None:
        """
            Инициализация менеджера. Может сразу принять конфигурацию.
            Args:
                raw_config: Сырые настройки (dict, объект, путь и т.д.)
        """
        from ..configs import FsmConfig
        self._config: Optional[FsmConfig] = None
        if raw_config: self.set_config(raw_config)
        self._fsms: list[Fsm] = []

    @property
    def state_configs(self) -> StateConfigDict:
        """ Словарь допустимых статусов и их настроек. """
        return self._config.state_configs

    def create_fsm(self, raw_config: Optional[Any] = None) -> Fsm:
        """
            Создаёт новую машину состояний и возвращает её.
            Args:
                raw_config: Необязательная индивидуальная конфигурация.
            Returns:
                Fsm: новая машина состояний.
        """
        self.set_config(raw_config)
        fsm = Fsm(self._config)
        self._fsms.append(fsm)
        return fsm

    def set_config(self, raw_config: Optional[Any] = None) -> None:
        """
            Устанавливает новую конфигурацию для последующих StateMachine.
            В случае ошибки или пустого конфига FSM выключается.
        """
        try:
            if raw_config:
                self._config = self._parse_raw_config(raw_config)
        except Exception as e:
            print(f"WARNING: FsmManager couldn't parse the raw_config. State machine OFF:\n{e}")
            if self._config is not None:
                self._config.enable = False
            return

        # Защита от ситуации, когда парсер вернул None
        if self._config is None:
            print("WARNING: FsmManager got None config. State machine OFF.")
            return

        # Если enable отсутствует или None — выключаем
        if getattr(self._config, "enable", None) is None:
            print("WARNING: Config 'enable' is None. State machine OFF.")
            self._config.enable = False

    @property
    def enable(self) -> bool:
        """ True, если включено использование машины состояний. """
        return self._config.enable if self._config else False

    def switch_profile_by_pid(self, pid: int) -> None:
        """ Сменить активный профиль по указанному pid для всех FSM """
        for fsm in self._fsms:
            fsm.switch_profile_by_pid(pid)

    def switch_profile_by_name(self, profile_name: ProfileNames | str) -> None:
        """ Сменить активный профиль у всех FSM по названию профиля. """
        for fsm in self._fsms:
            fsm.switch_profile_by_name(profile_name)




    def reset_all(self) -> None:
        """Сбросить все FSM."""
        for fsm in self._fsms:
            fsm.reset_all_states()

    def update_all(self, cls_id: int) -> None:
        """Отправить новое состояние всем FSM (если нужно массовое обновление, например, при синхронизации)."""
        for fsm in self._fsms:
            fsm.process_state(cls_id)

    def get_statuses(self) -> dict[int, str]:
        """Получить активные профили всех FSM."""
        return {i: fsm.active_profile.name for i, fsm in enumerate(self._fsms)}

    def destroy(self) -> None:
        """ Сбрасывает конфигурацию и список созданных машин. """
        self._config = None
        self._fsms.clear()

    @staticmethod
    def _parse_raw_config(raw_config: Any) -> 'FsmConfig':
        """ Парсит произвольный формат конфигурации в StateMachineConfig. """
        from ..config_parser.parser_factory import ParserFactory
        return ParserFactory.parse(raw_config)

    def __getitem__(self, idx: int) -> Fsm:
        return self._fsms[idx]

    def __len__(self) -> int:
        return len(self._fsms)
