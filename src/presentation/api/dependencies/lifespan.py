from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from infrastructure.config import APIWorkerSettings
from infrastructure.db.postgres import PostgresConnectionManager
from infrastructure.email import SimpleEmailBodyBuilder
from infrastructure.jwt.pyjwt import PyJWTManager
from infrastructure.key_value.redis import RedisConnectionManager
from infrastructure.masage_broker.nats import NatsConnectionManager
from infrastructure.password_manager import Argon2PasswordManager
from infrastructure.randomizer import SecureRandomizer


class APILifespan:
    def __init__(self, settings: APIWorkerSettings) -> None:
        self._settings: APIWorkerSettings = settings

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None]:
        pg_connection_manager = PostgresConnectionManager(self._settings.db)
        nats_connection_manager = NatsConnectionManager(self._settings.nats)
        redis_connection_manager = RedisConnectionManager(self._settings.redis)
        password_manager = Argon2PasswordManager()
        email_builder = SimpleEmailBodyBuilder()
        randomizer = SecureRandomizer()
        jwt_manager = PyJWTManager(self._settings.jwt)
        await pg_connection_manager.init()
        await redis_connection_manager.init()
        app.state.worker_settings = self._settings
        app.state.db_connection_manager = pg_connection_manager
        app.state.nats_connection_manager = nats_connection_manager
        app.state.redis_connection_manager = redis_connection_manager
        app.state.password_manager = password_manager
        app.state.email_builder = email_builder
        app.state.randomizer = randomizer
        app.state.jwt_manager = jwt_manager
        yield
        await pg_connection_manager.close()
        await nats_connection_manager.close()
        await redis_connection_manager.close()
