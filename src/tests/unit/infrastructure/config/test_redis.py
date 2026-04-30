from infrastructure.config.redis import RedisSettings


def test_redis_url_without_password() -> None:
    settings = RedisSettings(host="localhost", port=6379, db=1)

    assert settings.url == "redis://localhost:6379/1"


def test_redis_url_with_password() -> None:
    settings = RedisSettings(host="redis.local", port=6380, db=2, password="pwd")

    assert settings.url == "redis://:pwd@redis.local:6380/2"
