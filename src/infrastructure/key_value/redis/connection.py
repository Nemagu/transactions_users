import asyncio

from redis.asyncio import Redis

from application.errors import AppInternalError
from infrastructure.config import RedisSettings

from .errors import handle_redis_errors


class RedisConnectionManager:
    def __init__(self, settings: RedisSettings) -> None:
        self._settings = settings
        self._client: Redis | None = None

    @handle_redis_errors
    async def init(self) -> None:
        """Инициализирует подключение к Redis."""
        self._client = Redis.from_url(
            self._settings.url,
            decode_responses=self._settings.decode_responses,
            health_check_interval=self._settings.healthcheck_interval,
            socket_timeout=self._settings.socket_timeout,
            socket_connect_timeout=self._settings.socket_connect_timeout,
        )
        await self._client.ping()  # pyright: ignore[reportGeneralTypeIssues]

    def client(self) -> Redis:
        """Возвращает адаптер key-value хранилища."""
        if self._client is None:
            raise AppInternalError(
                msg="RedisConnectionManager не инициализирован",
                action="получение redis key-value адаптера",
            )
        return self._client

    @handle_redis_errors
    async def close(self) -> None:
        """Закрывает подключение к Redis."""
        if self._client is not None:
            await asyncio.wait_for(self._client.aclose(), timeout=5)
            self._client = None
