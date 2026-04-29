from datetime import timedelta

from redis.asyncio import Redis

from application.errors import AppInternalError
from application.ports.key_value_store import KeyValueStore, Value

from .errors import handle_redis_errors


class RedisKeyValueStore(KeyValueStore):
    def __init__(self, client: Redis) -> None:
        self._client = client

    @handle_redis_errors
    async def set(self, key: str, value: Value, duration: timedelta) -> None:
        """Сохраняет значение по ключу на ограниченное время."""
        await self._client.set(name=key, value=value, ex=duration)

    @handle_redis_errors
    async def get_int(self, key: str) -> int | None:
        """Возвращает значение ключа как целое число."""
        value = await self._client.get(key)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError as err:
            raise AppInternalError(
                msg="в redis сохранено нечисловое значение",
                action="чтение числового значения из redis",
                data={"key": key, "value": value},
                wrap_error=err,
            ) from err
