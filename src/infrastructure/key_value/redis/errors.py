from functools import wraps

from redis import RedisError

from application.errors import AppInternalError


def handle_redis_errors(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except RedisError as err:
            raise AppInternalError(
                msg=str(err),
                action="взаимодействие с redis",
                wrap_error=err,
            )

    return wrapper
