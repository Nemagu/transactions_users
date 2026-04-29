"""Модуль `infrastructure/config/db.py` слоя инфраструктуры."""

from os import path
from typing import Self

from pydantic import BaseModel, Field, model_validator


class PostgresPoolSettings(BaseModel):
    """Компонент `PostgresPoolSettings`."""
    min_size: int = 10
    max_size: int = 20
    max_inactive_connection_lifetime: int = 300
    max_connection_lifetime: int = 3600
    timeout: int = 20


class PostgresSettings(BaseModel):
    """Компонент `PostgresSettings`."""
    host: str = "localhost"
    port: int = 5432
    user: str = "transactions_users"
    password_file: str = "/tmp/transactions/db_password"
    database: str = "transactions_users"

    pool: PostgresPoolSettings = Field(default_factory=PostgresPoolSettings)

    @model_validator(mode="after")
    def validate_password_file(self) -> Self:
        """Описывает операцию `validate_password_file`."""
        if not path.isfile(self.password_file):
            raise ValueError(f"Password file not found: {self.password_file}")
        return self

    @property
    def password(self) -> str:
        """Описывает операцию `password`."""
        with open(self.password_file, "r", encoding="utf-8") as file:
            return file.read().strip()

    @property
    def url(self) -> str:
        """Описывает операцию `url`."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def url_with_psycopg(self) -> str:
        """Описывает операцию `url_with_psycopg`."""
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
