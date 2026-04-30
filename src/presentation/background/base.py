"""Модуль `presentation/background/base.py` слоя представления."""

import asyncio
import os
from abc import ABC, abstractmethod
from logging import getLogger
from signal import SIGINT, SIGTERM

logger = getLogger(__name__)


class BackgroundBaseWorker(ABC):
    """Компонент `BackgroundBaseWorker`."""
    def __init__(self, healthcheck_file: str) -> None:
        """
        Args:
            healthcheck_file (str): Значение `healthcheck_file`.
        """
        self._healthcheck_file = healthcheck_file
        self._shutdown_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = list()

    @abstractmethod
    async def setup(self) -> None: ...

    @abstractmethod
    async def complete(self) -> None: ...

    async def run(self) -> None:
        """Описывает операцию `run`."""
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(SIGTERM, self._handle_signal)
        loop.add_signal_handler(SIGINT, self._handle_signal)
        await self.setup()
        if self._shutdown_event.is_set():
            await self.complete()
            return
        logger.info("background worker started")
        self._create_tasks()
        await self._shutdown_event.wait()
        logger.info("shutting down...")
        await self._cancel_tasks()
        await self.complete()
        logger.info("background worker stopped")

    @abstractmethod
    def _create_tasks(self) -> None: ...

    async def _cancel_tasks(self) -> None:
        """Описывает операцию `_cancel_tasks`."""
        for task in self._tasks:
            task.cancel()
        errors = await asyncio.gather(*self._tasks, return_exceptions=True)
        for error in errors:
            if isinstance(error, asyncio.CancelledError):
                continue
            if isinstance(error, BaseException):
                logger.error("task cancelled error: %s", error)
        self._tasks.clear()

    def _handle_signal(self) -> None:
        """Описывает операцию `_handle_signal`."""
        logger.info("shutting down...")
        self._shutdown_event.set()

    def _update_heartbeat(self) -> None:
        """Описывает операцию `_update_heartbeat`."""
        try:
            open(self._healthcheck_file, "a").close()
            os.utime(self._healthcheck_file, None)
        except Exception as e:
            logger.error("failed to update heartbeat: %s", e)
