from __future__ import annotations

__all__ = ['Fsm']

from typing import Optional, Any

from ..config_parser.parsing_utils import normalize_enum_str
from ..configs import FsmConfig
from ..history_writer import HistoryWriterFactory
from ..models import ProfileNames
from ..models.result import FsmResult
from .profiles.profile_manager import ProfileManager
from .history import RawStateHistory
from .profiles.profile import Profile


class Fsm:
    """ Машина состояний, управляющая историей и счётчиками состояний """

    def __init__(self, config: FsmConfig) -> None:
        self._enable: bool = config.enable
        # self._cur_state: Optional[State] = None
        self._meta: dict[str, Any] = config.meta
        self._raw_history = RawStateHistory()
        self._profile_manager: ProfileManager = ProfileManager(
            state_configs=config.states,
            profile_configs=config.profile_configs,
            switcher_strategy=config.switcher_strategy,
            def_profile=config.def_profile,
            profile_ids_map=config.profile_ids_map
        )
        self._result: Optional[FsmResult] = None
        # Писатель сырой истории
        self._raw_history_writer = HistoryWriterFactory.create(config.raw_history_writer)
        # Писатель стабильной истории
        self._stable_history_writer = HistoryWriterFactory.create(config.stable_history_writer)
        # Записываем настройки в заголовок файла
        self._stable_history_writer.write_configs(config.to_dict())

    @property
    def active_profile(self) -> Profile:
        return self._profile_manager.active_profile

    def switch_profile_by_pid(self, pid: Optional[int]) -> None:
        """ Сменить активный профиль по указанному pid """
        self._profile_manager.switch_profile_by_pid(pid)

    def switch_profile_by_name(self, profile_name: ProfileNames | str) -> None:
        """ Сменить активный профиль по названию профиля. """
        profile_name = normalize_enum_str(profile_name, case="lower")
        self._profile_manager.switch_profile_by_name(profile_name)

    def process_state(self, cls_id: int) -> FsmResult:
        """
            Обрабатывает новое состояние машины состояний.
            Этапы обработки:
            1. Получение объекта состояния (`State`) по его идентификатору.
            2. Если состояние является триггером сброса — сбрасываются счётчики других состояний.
            3. Если состояние является триггером прерывания — возвращается флаг прерывания обработки.
            4. Если состояние стабильно — записывается в историю, остальные счётчики сбрасываются.
            5. Если история соответствует ожидаемой последовательности — подготавливается флаг события и
               сбрасываются все состояния.
            Args:
                cls_id (int): Идентификатор состояния, полученный от нейросети.
        """
        cur_state = self.active_profile.activate_state_by_id(cls_id)
        self.active_profile.increment_counter()

        # Добавляет состояние в сырую историю
        self._raw_history.add(cur_state)

        # Если текущее состояние является триггером для сброса, сбрасываем все счётчики сбрасываемых состояния, кроме текущего
        if self.active_profile.is_resetter:
            self.active_profile.reset_counters(only_resettable=True, except_cur_state=True)

        # Если текущее состояние стабильное, то прибавляем его счётчик, добавляем в историю и сбрасываем все счётчики состояний, кроме текущего
        if self.active_profile.is_stable:
            self.active_profile.add_active_state_to_history()
            self.active_profile.reset_counters(only_resettable=False, except_cur_state=True)

        # Если ожидаемая последовательность сработала, скидываем все счётчики и очищаем историю
        is_stage_done = self.active_profile.is_expected_seq_valid()
        if is_stage_done:
            self.active_profile.reset_counters(only_resettable=False, except_cur_state=False)
            self.active_profile.clear_history()
            self.active_profile.add_init_states_to_history()

        self._result = FsmResult(
            active_profile=self.active_profile.name,
            state=cur_state,
            resetter=self.active_profile.is_resetter,
            breaker=self.active_profile.is_breaker,
            stable=self.active_profile.is_stable,
            stage_done=is_stage_done,
            # counters=self.active_profile._counters.copy(),
        )

        self._raw_history_writer.write(str(cls_id))
        self._stable_history_writer.write(self._result.to_dict())

        return self._result
