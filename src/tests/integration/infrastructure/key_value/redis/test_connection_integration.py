from datetime import timedelta

import pytest

from infrastructure.key_value.redis.store import RedisKeyValueStore


@pytest.mark.asyncio
async def test_redis_connection_manager_init_and_client(redis_connection_manager) -> None:
    client = redis_connection_manager.client()

    assert await client.ping() is True


@pytest.mark.asyncio
async def test_redis_connection_manager_with_store(redis_connection_manager) -> None:
    store = RedisKeyValueStore(redis_connection_manager.client())

    await store.set("count", 11, timedelta(seconds=10))

    assert await store.get_int("count") == 11
