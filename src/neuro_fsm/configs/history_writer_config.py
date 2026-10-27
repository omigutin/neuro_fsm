__all__ = ['HistoryWriterConfig']

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HistoryWriterConfig:
    """
        Настройки писателя истории в файл.
        Поля:
            name: шаблон имени файла в каталоге ./fsm_logs, поддерживает подстановку {timestamp};
            fields: поля записи (используются асинхронным писателем сырой истории);
            enable: включена ли запись;
            max_age_days: файлы старше этого срока удаляются при создании писателя;
            async_mode: использовать асинхронный писатель (зарезервировано).
    """
    name: str = ""
    fields: tuple[str, ...] = ()
    enable: bool = False
    max_age_days: int = 14
    async_mode: bool = False

    def __post_init__(self) -> None:
        """ Проверяет, что у включённого писателя задано имя файла. """
        if self.enable and not self.name:
            raise ValueError("[HistoryWriterConfig] name must be set when writer is enabled")
        if self.max_age_days < 0:
            raise ValueError(f"[HistoryWriterConfig] max_age_days must be >= 0, got {self.max_age_days}")

    @classmethod
    def disabled(cls) -> 'HistoryWriterConfig':
        """ Конфигурация выключенного писателя. """
        return cls()
