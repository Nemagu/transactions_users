"""Точка входа сервиса users."""

import asyncio
from logging import basicConfig, getLogger
from os import getenv

from infrastructure.config import (
    APIWorkerSettings,
    LogLevel,
    MessageBrokerPublisherSettings,
)
from infrastructure.db.postgres import apply_migrations
from presentation.api.server import APIWorker
from presentation.background.nats import NatsPublisherWorker

logger = getLogger(__name__)


def _setup_logging(level: LogLevel) -> None:
    """Инициализирует базовую конфигурацию логирования."""
    basicConfig(level=level.value)


def _to_bool(value: str | None, default: bool) -> bool:
    """Преобразует строковую переменную окружения в bool."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _run_worker_with_uvloop(worker: NatsPublisherWorker) -> None:
    """Запускает background-воркер через uvloop при его доступности."""
    try:
        import uvloop

        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(worker.run())
        return
    except Exception:
        logger.warning("uvloop is unavailable, fallback to default asyncio loop")
    asyncio.run(worker.run())


def main() -> None:
    """Запускает API или NATS publisher воркер в зависимости от MODE."""
    mode = getenv("MODE", "api").strip().lower()
    apply_db = _to_bool(getenv("APPLY_MIGRATIONS"), default=True)

    if mode == "api":
        settings = APIWorkerSettings()
        _setup_logging(settings.logging.level)
        if apply_db:
            apply_migrations(settings.db)
        APIWorker(settings).run()
        return

    if mode == "nats_publisher":
        settings = MessageBrokerPublisherSettings()
        _setup_logging(settings.logging.level)
        if apply_db:
            apply_migrations(settings.db)
        _run_worker_with_uvloop(NatsPublisherWorker(settings))
        return

    raise RuntimeError(f"unsupported MODE: {mode}")


if __name__ == "__main__":
    main()
