from datetime import timedelta

import pytest

from infrastructure.key_value.redis.store import RedisKeyValueStore


@pytest.mark.asyncio
async def test_redis_store_set_and_get_int(redis_client) -> None:
    store = RedisKeyValueStore(redis_client)

    await store.set("attempts", 7, timedelta(seconds=30))

    assert await store.get_int("attempts") == 7


@pytest.mark.asyncio
async def test_redis_store_get_int_returns_none(redis_client) -> None:
    store = RedisKeyValueStore(redis_client)

    assert await store.get_int("missing") is None
