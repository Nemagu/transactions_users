"""Модуль `infrastructure/config/nats.py` слоя инфраструктуры."""

from pydantic import BaseModel, Field


class CompanyNatsConsumerStreamSettings(BaseModel):
    """Настройки stream/subject для событий компании."""
    stream_name: str = "companies_service"
    main_subject_name: str = "company"
    creation_subject_name: str = "created"
    deletion_subject_name: str = "deleted"
    restoration_subject_name: str = "restored"

    @property
    def creation_subject(self) -> str:
        return (
            f"{self.stream_name}.{self.main_subject_name}.{self.creation_subject_name}"
        )

    @property
    def deletion_subject(self) -> str:
        return (
            f"{self.stream_name}.{self.main_subject_name}.{self.deletion_subject_name}"
        )

    @property
    def restoration_subject(self) -> str:
        return f"{self.stream_name}.{self.main_subject_name}.{self.restoration_subject_name}"


class EmployeeNatsConsumerStreamSettings(BaseModel):
    """Настройки stream/subject для событий сотрудника."""
    stream_name: str = "companies_service"
    main_subject_name: str = "employee"
    creation_subject_name: str = "created"
    deletion_subject_name: str = "dismissed"
    restoration_subject_name: str = "reinstated"

    @property
    def creation_subject(self) -> str:
        return (
            f"{self.stream_name}.{self.main_subject_name}.{self.creation_subject_name}"
        )

    @property
    def deletion_subject(self) -> str:
        return (
            f"{self.stream_name}.{self.main_subject_name}.{self.deletion_subject_name}"
        )

    @property
    def restoration_subject(self) -> str:
        return f"{self.stream_name}.{self.main_subject_name}.{self.restoration_subject_name}"


class ProjectNatsConsumerStreamSettings(BaseModel):
    """Настройки stream/subject для событий проекта."""
    stream_name: str = "time_tracker"
    main_subject_name: str = "project"
    creation_subject_name: str = "created"

    @property
    def creation_subject(self) -> str:
        return (
            f"{self.stream_name}.{self.main_subject_name}.{self.creation_subject_name}"
        )


class NatsConsumerStreamSettings(BaseModel):
    """Конфигурация входящих NATS stream-ов."""
    company: CompanyNatsConsumerStreamSettings = Field(
        default_factory=CompanyNatsConsumerStreamSettings
    )
    employee: EmployeeNatsConsumerStreamSettings = Field(
        default_factory=EmployeeNatsConsumerStreamSettings
    )
    project: ProjectNatsConsumerStreamSettings = Field(
        default_factory=ProjectNatsConsumerStreamSettings
    )


class BaseNatsPublisherStreamSettings(BaseModel):
    """Базовая конфигурация исходящих subject-ов."""
    stream_name: str = "projects_service"
    main_subject_name: str = ""
    creation_subject_name: str = "created"
    update_subject_name: str = "updated"
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
            self.deletion_subject,
            self.restoration_subject,
        ]


class ProjectNatsPublisherStreamSettings(BaseNatsPublisherStreamSettings):
    """Настройки публикации событий проекта."""
    main_subject_name: str = "project"


class ProjectSectionPublisherStreamSettings(BaseNatsPublisherStreamSettings):
    """Настройки публикации событий раздела проекта."""
    main_subject_name: str = "section"


class ProjectDisciplinePublisherStreamSettings(BaseNatsPublisherStreamSettings):
    """Настройки публикации событий дисциплины проекта."""
    main_subject_name: str = "discipline"


class ProjectStagePublisherStreamSettings(BaseNatsPublisherStreamSettings):
    """Настройки публикации событий этапа проекта."""
    main_subject_name: str = "stage"


class ProjectPartPublisherStreamSettings(BaseNatsPublisherStreamSettings):
    """Настройки публикации событий части проекта."""
    main_subject_name: str = "part"


class NatsPublisherStreamSettings(BaseModel):
    """Конфигурация исходящих NATS stream-ов."""
    project: ProjectNatsPublisherStreamSettings = Field(
        default_factory=ProjectNatsPublisherStreamSettings
    )
    section: ProjectSectionPublisherStreamSettings = Field(
        default_factory=ProjectSectionPublisherStreamSettings
    )
    discipline: ProjectDisciplinePublisherStreamSettings = Field(
        default_factory=ProjectDisciplinePublisherStreamSettings
    )
    stage: ProjectStagePublisherStreamSettings = Field(
        default_factory=ProjectStagePublisherStreamSettings
    )
    part: ProjectPartPublisherStreamSettings = Field(
        default_factory=ProjectPartPublisherStreamSettings
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
