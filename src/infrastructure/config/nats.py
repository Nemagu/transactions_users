"""Модуль `infrastructure/config/nats.py` слоя инфраструктуры."""

from pydantic import BaseModel, Field


class BaseNatsPublisherStreamSettings(BaseModel):
    """Базовая конфигурация исходящих subject-ов."""

    stream_name: str = "users"
    main_subject_name: str = ""
    creation_subject_name: str = "created"
    update_subject_name: str = "updated"
    frozen_subject_name: str = "frozen"
    deletion_subject_name: str = "deleted"
    restoration_subject_name: str = "restored"

    @property
    def creation_subject(self) -> str:
        return (
            f"{self.stream_name}.{self.main_subject_name}.{self.creation_subject_name}"
        )

    @property
    def update_subject(self) -> str:
        return f"{self.stream_name}.{self.main_subject_name}.{self.update_subject_name}"

    @property
    def frozen_subject(self) -> str:
        return f"{self.stream_name}.{self.main_subject_name}.{self.frozen_subject_name}"

    @property
    def deletion_subject(self) -> str:
        return (
            f"{self.stream_name}.{self.main_subject_name}.{self.deletion_subject_name}"
        )

    @property
    def restoration_subject(self) -> str:
        return f"{self.stream_name}.{self.main_subject_name}.{self.restoration_subject_name}"

    @property
    def subjects(self) -> list[str]:
        return [
            self.creation_subject,
            self.update_subject,
            self.frozen_subject,
            self.deletion_subject,
            self.restoration_subject,
        ]


class UserNatsPublisherStreamSettings(BaseNatsPublisherStreamSettings):
    """Настройки публикации событий пользователя."""

    main_subject_name: str = "user"


class NatsPublisherStreamSettings(BaseModel):
    """Конфигурация исходящих NATS stream-ов."""

    user: UserNatsPublisherStreamSettings = Field(
        default_factory=UserNatsPublisherStreamSettings
    )


class NatsSettings(BaseModel):
    """Параметры подключения к NATS."""

    host: str = "localhost"
    port: int = 4222
    healthcheck_file: str = "/tmp/nats_worker_healthbeat"

    loop_sleep_duration: int = 2

    connect_name: str = "transactions"
    reconnect_time_wait: int = 5
    connect_timeout: int = 5
    ping_interval: int = 120
    max_outstanding_pings: int = 3

    @property
    def url(self) -> str:
        return f"nats://{self.host}:{self.port}"
