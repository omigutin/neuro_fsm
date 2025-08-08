from __future__ import annotations

__all__ = ['Fsm']

from typing import Optional, Any

from ..config_parser.parsing_utils import normalize_enum_str
from ..configs import FsmConfig
from ..history_writer import StableHistoryWriter, RawHistoryWriter
from ..models import ProfileNames
from ..models.result import FsmResult
from .profiles.profile_manager import ProfileManager
from .history import RawStateHistory


class Fsm:
    """
        Главный управляющий компонент машины состояний.
        Отвечает за:
        - Обработку входных состояний от нейросети;
        - Управление активным профилем (включая автоматическое и ручное переключение);
        - Ведение сырой и стабильной истории;
        - Формирование результата обработки (`FsmResult`).
        Все бизнес-решения и сценарии обработки происходят на этом уровне.
    """

    def __init__(self, config: FsmConfig) -> None:
        """
            Инициализация машины состояний на основе переданной конфигурации.
            Args:
                config (FsmConfig): Конфигурация, содержащая состояния, профили, стратегию переключения
                                    и настройки логирования.
        """
        self._enable: bool = config.enable
        self._meta: dict[str, Any] = config.meta
        self._raw_history = RawStateHistory()

        self._profile_manager: ProfileManager = ProfileManager(
            state_configs=config.states,
            profile_configs=config.profile_configs,
            switcher_strategy=config.switcher_strategy,
            def_profile=config.def_profile,
            profile_ids_map=config.profile_ids_map
        )

        # Писатель сырой истории
        self._raw_history_writer = RawHistoryWriter(config.raw_history_writer)
        # Писатель стабильной истории
        self._stable_history_writer = StableHistoryWriter(config.stable_history_writer)
        # Записываем настройки и конфигурацию профилей
        self._stable_history_writer.write_configs(config.to_dict())
        self._stable_history_writer.write_profile_configs(self._profile_manager._profiles)

    # @property
    # def active_profile(self) -> Profile:
    #     """ Возвращает текущий активный профиль машины состояний. """
    #     return self._profile_manager.active_profile

    def switch_profile_by_pid(self, pid: Optional[int]) -> None:
        """ Сменить активный профиль по id продукции (используется при ручной или полуавтоматической стратегии). """
        self._profile_manager.switch_profile_by_pid(pid)

    def switch_profile_by_name(self, profile_name: ProfileNames | str) -> None:
        """ Сменить активный профиль по имени. """
        profile_name = normalize_enum_str(profile_name, case="lower")
        self._profile_manager.switch_profile_by_name(profile_name)

    def process_state(self, cls_id: int) -> FsmResult:
        """
            Основной метод обработки входного состояния от нейросети.
            Обновляет счётчики, историю, переключает профили (при необходимости), и возвращает результат обработки.
            Этапы:
            1. Активирует состояние по `cls_id`;
            2. Увеличивает счётчик;
            3. Записывает в сырую историю;
            4. Обрабатывает триггеры (reset, stable, break);
            5. Проверяет, сработала ли ожидаемая последовательность.
            Args:
                cls_id (int): Идентификатор класса состояния от нейросети.
            Returns:
                FsmResult: Результат обработки (для стабильной истории или внешней логики).
        """
        is_profile_changed: bool = False

        self._profile_manager.register_state(cls_id)

        self._raw_history_writer.write(str(cls_id))
        self._stable_history_writer.write_state(self._profile_manager.active_profile.cur_state)

        # Добавляет состояние в сырую историю
        self._raw_history.add(self._profile_manager.active_profile.cur_state)

        # Если текущее состояние является триггером для сброса, сбрасываем все счётчики сбрасываемых состояния, кроме текущего
        self._profile_manager.reset_by_trigger()

        # Если текущее состояние стабильное, то прибавляем его счётчик, добавляем в историю и сбрасываем все счётчики состояний, кроме текущего
        self._profile_manager.commit_stable_states()

        # Проверяем, сработала ли последовательность из активного профиля
        stage_done = self._profile_manager.active_profile.is_expected_seq_valid()
        if not stage_done:
            # Если ожидаемая последовательность сработала, то проверяем не надо ли сменить активный профиль
            is_profile_changed = self._profile_manager.update_active_profile()
            if is_profile_changed:
                # self._raw_history.recalculate_for(self._profile_manager.active_profile)
                self._profile_manager.active_profile.reset_to_init_state()

        self._stable_history_writer.write_runtime(self._profile_manager.active_profile, self._profile_manager)

        return FsmResult(
            active_profile=self._profile_manager.active_profile.name,
            state=self._profile_manager.active_profile.cur_state,
            resetter=self._profile_manager.active_profile.is_resetter,
            breaker=self._profile_manager.active_profile.is_breaker,
            stable=self._profile_manager.active_profile.is_stable,
            is_profile_changed=is_profile_changed,
            stage_done=stage_done,
            # counters=self._profile_manager.active_profile._counters.copy(),
        )
