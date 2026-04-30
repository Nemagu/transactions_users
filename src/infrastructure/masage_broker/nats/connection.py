import asyncio

from nats import connect
from nats.aio.client import Client
from nats.js import JetStreamContext

from application.errors import AppInternalError
from infrastructure.config import NatsSettings


class NatsConnectionManager:
    def __init__(self, settings: NatsSettings) -> None:
        self._nats_settings = settings
        self._nc = None

    async def client(self) -> Client:
        if self._nc is None or not self._nc.is_connected:
            await self._connect()
        return self._nc  # pyright: ignore[reportReturnType]

    async def client_with_jetstream(self) -> tuple[Client, JetStreamContext]:
        if self._nc is None or not self._nc.is_connected:
            await self._connect()
        return self._nc, self._nc.jetstream()  # pyright: ignore[reportOptionalMemberAccess, reportUnknownMemberType, reportReturnType]

    async def close(self) -> None:
        if self._nc is None:
            return
        await asyncio.wait_for(self._nc.close(), timeout=5.0)

    async def _connect(self) -> None:
        try:
            self._nc = await asyncio.wait_for(
                connect(
                    self._nats_settings.url,
                    name=self._nats_settings.connect_name,
                    connect_timeout=self._nats_settings.connect_timeout,
                    reconnect_time_wait=self._nats_settings.reconnect_time_wait,
                    max_reconnect_attempts=0,
                    ping_interval=self._nats_settings.ping_interval,
                    max_outstanding_pings=self._nats_settings.max_outstanding_pings,
                ),
                timeout=self._nats_settings.connect_timeout,
            )
        except BaseException as err:
            raise AppInternalError(
                msg="ошибка подключения к nats",
                action="подключение к nats",
                wrap_error=err,
            ) from err
