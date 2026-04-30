from fastapi import Request

from infrastructure.key_value.redis import RedisKeyValueStore


async def redis_store(request: Request) -> RedisKeyValueStore:
    return RedisKeyValueStore(request.app.state.redis_connection_manager.client())
