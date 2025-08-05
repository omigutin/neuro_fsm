from __future__ import annotations

__all__ = ['Fsm']

from typing import Optional, Any

from ..config_parser.parsing_utils import normalize_enum_str
from ..history_writer import HistoryWriterFactory
from ..models import ProfileNames
from ..models.result import FsmResult
from .profiles.profile_manager import ProfileManager
from .history import RawStateHistory
from .profiles.profile import Profile


class Fsm:
    """ Машина состояний, управляющая историей и счётчиками состояний """

    def __init__(self, config: 'FsmConfig') -> None:
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

    def switch_profile_by_pid(self, pid: Optional[int]) -> None:
        """ Сменить активный профиль по указанному pid """
        self._profile_manager.switch_profile_by_pid(pid)

    def switch_profile_by_name(self, profile_name: ProfileNames | str) -> None:
        """ Сменить активный профиль по названию профиля. """
        profile_name = normalize_enum_str(profile_name, case="lower")
        self._profile_manager.switch_profile_by_name(profile_name)

    @property
    def active_profile(self) -> Profile:
        return self._profile_manager.active_profile

    # @property
    # def profile_manager(self) -> ProfileManager:
    #     return self._profile_manager

    # @property
    # def cur_state(self) -> Optional[State]:
    #     return self._cur_state

    @property
    def result(self) -> Optional[FsmResult]:
        return self._result

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
                cls_id (StateOrIdType): Идентификатор или объект состояния, полученный от нейросети.
            Returns:
                tuple[bool, bool]:
                    - Первый элемент — `True`, если сработала последовательность и нужно отправить событие.
                    - Второй элемент — `True`, если необходимо прервать обработку (например, отсутствует объект).
        """
        cur_state = self.active_profile.set_cur_state_by_cls_id(cls_id)
        self.active_profile.increment_counter()

        # Добавляет состояние в сырую историю
        self._raw_history.add(cur_state)

        # Если текущее состояние является триггером для сброса, сбрасываем все счётчики сбрасываемых состояния, кроме текущего
        is_resetter = self.active_profile.is_reset_trigger()
        if is_resetter:
            self.active_profile.reset_counters(only_resettable=True, except_cur_state=True)

        # Если текущее состояние стабильное, то прибавляем его счётчик, добавляем в историю и сбрасываем все счётчики состояний, кроме текущего
        stable = self._handle_stable_state()
        # Если ожидаемая последовательность сработала, скидываем все счётчики и очищаем историю
        stage_done = self._handle_expected_seq_completion()
        # Выясняем, является ли текущее состояние триггером для прерывания поиска
        breaker = self._handle_break_trigger()

        self._result = FsmResult(
            active_profile=self.active_profile.name,
            state=cur_state,
            resetter=is_resetter,
            breaker=breaker,
            stable=stable,
            stage_done=stage_done,
            # counters=self.active_profile._counters.copy(),
        )

        self._raw_history_writer.write(str(cls_id))
        self._stable_history_writer.write(self._result.to_dict())

        return self._result

    # def _get_state(self, cls_id: int) -> State:
    #     return self._states[cls_id]

    # def _handle_reset_trigger(self) -> bool:
    #     ret = False
    #     if self.active_profile.is_reset_trigger():
    #         self.active_profile.reset_counters(only_resettable=True, except_cur_state=True)
    #         ret = True
    #     return ret

    # def _handle_break_trigger(self) -> bool:
    #     return self.active_profile.is_break_trigger()

    def _handle_stable_state(self) -> bool:
        ret = False
        if self.active_profile.is_state_stable():
            self.active_profile.add_to_history()
            self.active_profile.reset_counters(only_resettable=False, except_cur_state=True)
            ret = True
        return ret

    def _handle_expected_seq_completion(self) -> bool:
        if self.active_profile.is_expected_seq_valid():
            self.active_profile.reset_counters_and_clear_history()
            return True
        return False
