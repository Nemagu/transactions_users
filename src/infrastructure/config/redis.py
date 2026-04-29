"""Модуль `infrastructure/config/redis.py` слоя инфраструктуры."""

from pydantic import BaseModel


class RedisSettings(BaseModel):
    """Компонент `RedisSettings`."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    decode_responses: bool = True
    healthcheck_interval: int = 30
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    @property
    def url(self) -> str:
        """Возвращает URL подключения к Redis."""
        auth = ""
        if self.password is not None:
            auth = f":{self.password}@"
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
