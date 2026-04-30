"""Модель настроек логирования инфраструктурного слоя."""

from enum import StrEnum

from pydantic import BaseModel


class LogLevel(StrEnum):
    """Поддерживаемые уровни логирования приложения."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LoggingSettings(BaseModel):
    """Настройки логирования приложения."""

    level: LogLevel = LogLevel.INFO
