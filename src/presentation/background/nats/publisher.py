"""NATS publisher worker для публикации user-событий."""

import asyncio
from logging import getLogger

from nats.js.api import StreamConfig
from nats.js.errors import NotFoundError

from application.command.private.user import UserPublicationUseCase
from application.errors import AppError, AppInternalError
from domain.errors import DomainError
from infrastructure.config import MessageBrokerPublisherSettings
from infrastructure.db.postgres import PostgresUnitOfWork
from infrastructure.masage_broker.nats import EventNatsPublisher
from presentation.background.nats.base import NATS_CONNECTION_ERRORS, NatsBaseWorker

logger = getLogger(__name__)


class NatsPublisherWorker(NatsBaseWorker):
    """Воркер публикации событий пользователей в NATS."""

    def __init__(self, settings: MessageBrokerPublisherSettings) -> None:
        super().__init__(settings.nats, settings.db)
        self._publishers_settings = settings.publishers

    async def _events_after_connected(self) -> None:
        await self._ensure_stream()

    async def _ensure_stream(self) -> None:
        stream = self._publishers_settings.user
        assert self._js is not None
        try:
            await self._js.stream_info(stream.stream_name)
        except NotFoundError:
            await self._js.add_stream(
                config=StreamConfig(name=stream.stream_name, subjects=stream.subjects)
            )

    def _create_tasks(self) -> None:
        self._tasks.append(asyncio.create_task(self._publish_loop()))

    async def _publish_loop(self) -> None:
        while not self._shutdown_event.is_set():
            self._update_heartbeat()
            try:
                await self._publish_once()
            except NATS_CONNECTION_ERRORS:
                logger.warning("nats connection lost, reconnecting")
                await self._connect_nats()
                continue
            except asyncio.CancelledError:
                return
            except BaseException as err:
                self._log_processing_error(err)
            await asyncio.sleep(self._nats_settings.loop_sleep_duration)

    async def _publish_once(self) -> None:
        assert self._js is not None
        async with self._db_manager.connection() as conn:
            await UserPublicationUseCase(
                PostgresUnitOfWork(conn),
                EventNatsPublisher(
                    stream_settings=self._publishers_settings,
                    nc=self._nc,  # pyright: ignore[reportArgumentType]
                    js=self._js,
                ),
            ).execute()

    def _log_processing_error(self, error: BaseException) -> None:
        if isinstance(error, DomainError):
            logger.warning(
                "domain error: %s, struct_name: %s, data=%s",
                error.msg,
                error.struct_name,
                error.data,
            )
            return
        if isinstance(error, AppInternalError):
            logger.error(
                "app internal error: %s, action: %s, data=%s",
                error.msg,
                error.action,
                error.data,
            )
            return
        if isinstance(error, AppError):
            logger.warning(
                "app error: %s, action: %s, data=%s",
                error.msg,
                error.action,
                error.data,
            )
            return
        logger.error("worker error: %s", error)
