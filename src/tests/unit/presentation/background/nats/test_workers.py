from pathlib import Path
from types import SimpleNamespace

import pytest
from nats.errors import ConnectionClosedError
from nats.js.errors import NotFoundError

from application.errors import AppError, AppInternalError
from domain.errors import DomainError
from infrastructure.config.db import PostgresSettings
from infrastructure.config.nats import NatsPublisherStreamSettings, NatsSettings
from presentation.background.nats.base import NatsBaseWorker
from presentation.background.nats.publisher import NatsPublisherWorker


class _FakeDbManager:
    async def init(self) -> None:
        return None

    async def close(self) -> None:
        return None


class _TestNatsWorker(NatsBaseWorker):
    async def _events_after_connected(self) -> None:
        return None

    def _create_tasks(self) -> None:
        return None


@pytest.fixture
def pg_settings(tmp_path: Path) -> PostgresSettings:
    password_file = tmp_path / "pwd.txt"
    password_file.write_text("secret", encoding="utf-8")
    return PostgresSettings(password_file=str(password_file))


@pytest.mark.asyncio
async def test_connect_nats_sets_connection(monkeypatch: pytest.MonkeyPatch, pg_settings):
    worker = _TestNatsWorker(NatsSettings(), pg_settings)
    worker._db_manager = _FakeDbManager()

    class _Nc:
        is_connected = True

        def jetstream(self):
            return "js"

    async def fake_connect(*args, **kwargs):
        return _Nc()

    monkeypatch.setattr("presentation.background.nats.base.connect", fake_connect)

    await worker._connect_nats()

    assert worker._nc is not None
    assert worker._js == "js"


@pytest.mark.asyncio
async def test_connect_nats_retries_until_shutdown(
    monkeypatch: pytest.MonkeyPatch,
    pg_settings,
):
    worker = _TestNatsWorker(NatsSettings(reconnect_time_wait=1), pg_settings)
    worker._db_manager = _FakeDbManager()
    calls = {"count": 0}

    async def fake_connect(*args, **kwargs):
        calls["count"] += 1
        worker._shutdown_event.set()
        raise RuntimeError("boom")

    monkeypatch.setattr("presentation.background.nats.base.connect", fake_connect)

    await worker._connect_nats()

    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_publisher_ensure_stream_creates_when_missing(pg_settings):
    settings = SimpleNamespace(
        nats=NatsSettings(),
        db=pg_settings,
        publishers=NatsPublisherStreamSettings(),
    )
    worker = NatsPublisherWorker(settings)

    created = {"value": False}

    class _Js:
        async def stream_info(self, name: str):
            raise NotFoundError

        async def add_stream(self, config):
            created["value"] = True

    worker._js = _Js()

    await worker._ensure_stream()

    assert created["value"] is True


def test_publisher_log_processing_error_handles_known_errors(pg_settings):
    settings = SimpleNamespace(
        nats=NatsSettings(),
        db=pg_settings,
        publishers=NatsPublisherStreamSettings(),
    )
    worker = NatsPublisherWorker(settings)

    worker._log_processing_error(DomainError(msg="x", struct_name="s"))
    worker._log_processing_error(AppInternalError(msg="x", action="a"))
    worker._log_processing_error(AppError(msg="x", action="a"))
    worker._log_processing_error(RuntimeError("x"))


@pytest.mark.asyncio
async def test_publish_loop_recovers_on_nats_connection_error(
    monkeypatch: pytest.MonkeyPatch,
    pg_settings,
):
    settings = SimpleNamespace(
        nats=NatsSettings(loop_sleep_duration=0),
        db=pg_settings,
        publishers=NatsPublisherStreamSettings(),
    )
    worker = NatsPublisherWorker(settings)

    calls = {"reconnect": 0}

    async def fake_publish_once():
        worker._shutdown_event.set()
        raise ConnectionClosedError()

    async def fake_connect_nats():
        calls["reconnect"] += 1

    monkeypatch.setattr(worker, "_publish_once", fake_publish_once)
    monkeypatch.setattr(worker, "_connect_nats", fake_connect_nats)

    await worker._publish_loop()

    assert calls["reconnect"] == 1
