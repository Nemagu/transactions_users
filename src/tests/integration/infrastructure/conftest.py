from collections.abc import AsyncGenerator

import pytest_asyncio
from nats import connect
from nats.aio.client import Client
from nats.js.client import JetStreamContext

from infrastructure.key_value.redis.connection import RedisConnectionManager


@pytest_asyncio.fixture
async def nats_client(nats_settings) -> AsyncGenerator[Client, None]:
    nc = await connect(nats_settings.url, name="users_integration_tests")
    try:
        yield nc
    finally:
        await nc.close()


@pytest_asyncio.fixture
async def nats_jetstream(nats_client: Client) -> JetStreamContext:
    return nats_client.jetstream()


@pytest_asyncio.fixture
async def redis_connection_manager(redis_settings) -> AsyncGenerator[RedisConnectionManager, None]:
    manager = RedisConnectionManager(redis_settings)
    await manager.init()
    try:
        yield manager
    finally:
        await manager.close()
