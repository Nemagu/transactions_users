"""Модуль `infrastructure/config/__init__.py` слоя инфраструктуры."""

from os import getenv

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from infrastructure.config.db import PostgresPoolSettings, PostgresSettings
from infrastructure.config.fastapi import FastAPISettings, UvicornSettings
from infrastructure.config.nats import (
    CompanyNatsConsumerStreamSettings,
    EmployeeNatsConsumerStreamSettings,
    NatsConsumerStreamSettings,
    NatsPublisherStreamSettings,
    NatsSettings,
    ProjectDisciplinePublisherStreamSettings,
    ProjectNatsConsumerStreamSettings,
    ProjectNatsPublisherStreamSettings,
    ProjectPartPublisherStreamSettings,
    ProjectSectionPublisherStreamSettings,
    ProjectStagePublisherStreamSettings,
)

__all__ = [
    "APIWorkerSettings",
    "CompanyNatsConsumerStreamSettings",
    "EmployeeNatsConsumerStreamSettings",
    "FastAPISettings",
    "MessageBrokerPublisherSettings",
    "NatsConsumerStreamSettings",
    "NatsPublisherStreamSettings",
    "NatsSettings",
    "PostgresPoolSettings",
    "PostgresSettings",
    "ProjectDisciplinePublisherStreamSettings",
    "ProjectNatsConsumerStreamSettings",
    "ProjectNatsPublisherStreamSettings",
    "ProjectPartPublisherStreamSettings",
    "ProjectSectionPublisherStreamSettings",
    "ProjectStagePublisherStreamSettings",
    "UvicornSettings",
]


class AppBaseSettings(BaseSettings):
    """Компонент `AppBaseSettings`."""

    model_config = SettingsConfigDict(
        yaml_file=getenv("CONFIG_FILE"),
        yaml_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Описывает операцию `settings_customise_sources`."""
        return (
            YamlConfigSettingsSource(
                settings_cls=settings_cls,
                yaml_file=getenv("CONFIG_FILE"),
                yaml_file_encoding="utf-8",
            ),
        )


class APIWorkerSettings(AppBaseSettings):
    """Компонент `APIWorkerSettings`."""

    fastapi: FastAPISettings = Field(default_factory=FastAPISettings)
    uvicorn: UvicornSettings = Field(default_factory=UvicornSettings)
    db: PostgresSettings = Field(default_factory=PostgresSettings)


class MessageBrokerConsumerSettings(AppBaseSettings):
    """Компонент `MessageBrokerConsumerSettings`."""

    nats: NatsSettings = Field(default_factory=NatsSettings)
    consumers: NatsConsumerStreamSettings = Field(
        default_factory=NatsConsumerStreamSettings
    )
    db: PostgresSettings = Field(default_factory=PostgresSettings)


class MessageBrokerPublisherSettings(AppBaseSettings):
    """Компонент `MessageBrokerPublisherSettings`."""

    nats: NatsSettings = Field(default_factory=NatsSettings)
    publishers: NatsPublisherStreamSettings = Field(
        default_factory=NatsPublisherStreamSettings
    )
    db: PostgresSettings = Field(default_factory=PostgresSettings)
