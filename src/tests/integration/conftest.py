from __future__ import annotations

import secrets
import shutil
import socket
import subprocess
import time
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from uuid import uuid7

import psycopg
import pytest
from psycopg.rows import dict_row
from redis.asyncio import Redis

from domain.user import Email, UserFactory, UserID
from infrastructure.config import NatsSettings, PostgresSettings, RedisSettings
from infrastructure.db.postgres.apply_migrations import apply_migrations

RUNTIME_DIR = Path("/tmp/users")
POSTGRES_USER = "users"
POSTGRES_DB = "users"


class IntegrationRuntime:
    def __init__(self) -> None:
        token = str(uuid7())
        self.project = f"users_tests_{token.replace('-', '_')}"
        self.compose_file = RUNTIME_DIR / f"docker-compose-{token}.yaml"
        self.postgres_password_file = RUNTIME_DIR / f"db-password-{token}.txt"
        self.postgres_config_file = RUNTIME_DIR / f"postgres-config-{token}.yaml"
        self.nats_config_file = RUNTIME_DIR / f"nats-config-{token}.yaml"
        self.redis_config_file = RUNTIME_DIR / f"redis-config-{token}.yaml"
        self.postgres_port = _choose_free_port()
        self.nats_port = _choose_free_port()
        self.redis_port = _choose_free_port()
        self.postgres_password = secrets.token_urlsafe(24)

    @property
    def postgres_settings(self) -> PostgresSettings:
        return PostgresSettings(
            host="127.0.0.1",
            port=self.postgres_port,
            user=POSTGRES_USER,
            database=POSTGRES_DB,
            password_file=str(self.postgres_password_file),
        )

    @property
    def nats_settings(self) -> NatsSettings:
        return NatsSettings(host="127.0.0.1", port=self.nats_port)

    @property
    def redis_settings(self) -> RedisSettings:
        return RedisSettings(host="127.0.0.1", port=self.redis_port)


def _choose_free_port() -> int:
    for _ in range(2000):
        port = secrets.randbelow(63000 - 2000 + 1) + 2000
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("Не удалось подобрать свободный порт")


def _run_compose(runtime: IntegrationRuntime, *args: str) -> None:
    command = [
        "docker",
        "compose",
        "-p",
        runtime.project,
        "-f",
        str(runtime.compose_file),
        *args,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Команда docker compose завершилась с ошибкой:\n"
            f"cmd: {' '.join(command)}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


def _write_runtime_files(runtime: IntegrationRuntime) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    runtime.postgres_password_file.write_text(runtime.postgres_password, encoding="utf-8")

    compose = f"""services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_USER: {POSTGRES_USER}
      POSTGRES_DB: {POSTGRES_DB}
      POSTGRES_PASSWORD: {runtime.postgres_password}
    ports:
      - \"{runtime.postgres_port}:5432\"
    healthcheck:
      test: [\"CMD-SHELL\", \"pg_isready -U {POSTGRES_USER} -d {POSTGRES_DB}\"]
      interval: 2s
      timeout: 3s
      retries: 30
      start_period: 2s
  nats:
    image: nats:2.12-alpine
    command: [\"-js\", \"-sd\", \"/data\"]
    ports:
      - \"{runtime.nats_port}:4222\"
  redis:
    image: redis:8.6-alpine
    ports:
      - \"{runtime.redis_port}:6379\"
"""
    runtime.compose_file.write_text(compose, encoding="utf-8")

    runtime.postgres_config_file.write_text(
        f"""db:
  host: 127.0.0.1
  port: {runtime.postgres_port}
  user: {POSTGRES_USER}
  database: {POSTGRES_DB}
  password_file: {runtime.postgres_password_file}
""",
        encoding="utf-8",
    )
    runtime.nats_config_file.write_text(
        f"""nats:
  host: 127.0.0.1
  port: {runtime.nats_port}
""",
        encoding="utf-8",
    )
    runtime.redis_config_file.write_text(
        f"""redis:
  host: 127.0.0.1
  port: {runtime.redis_port}
  db: 0
""",
        encoding="utf-8",
    )


def _wait_postgres_ready(settings: PostgresSettings) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(settings.url, connect_timeout=1) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return
        except Exception:
            time.sleep(1)
    raise TimeoutError("PostgreSQL не стал доступен за отведенное время")


def _wait_nats_ready(port: int) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1) as sock:
                sock.settimeout(1)
                if b"INFO" in sock.recv(1024):
                    return
        except Exception:
            time.sleep(1)
    raise TimeoutError("NATS не стал доступен за отведенное время")


def _wait_redis_ready(port: int) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except Exception:
            time.sleep(1)
    raise TimeoutError("Redis не стал доступен за отведенное время")


@pytest.fixture(scope="session")
def integration_runtime() -> Generator[IntegrationRuntime, None, None]:
    runtime = IntegrationRuntime()
    _write_runtime_files(runtime)
    _run_compose(runtime, "up", "-d")
    try:
        _wait_postgres_ready(runtime.postgres_settings)
        _wait_nats_ready(runtime.nats_port)
        _wait_redis_ready(runtime.redis_port)
        apply_migrations(runtime.postgres_settings)
        yield runtime
    finally:
        try:
            _run_compose(runtime, "down", "-v", "--remove-orphans")
        finally:
            for path in (
                runtime.compose_file,
                runtime.postgres_password_file,
                runtime.postgres_config_file,
                runtime.nats_config_file,
                runtime.redis_config_file,
            ):
                path.unlink(missing_ok=True)
            if RUNTIME_DIR.exists() and not any(RUNTIME_DIR.iterdir()):
                shutil.rmtree(RUNTIME_DIR, ignore_errors=True)


@pytest.fixture(scope="session")
def postgres_settings(integration_runtime: IntegrationRuntime) -> PostgresSettings:
    return integration_runtime.postgres_settings


@pytest.fixture(scope="session")
def nats_settings(integration_runtime: IntegrationRuntime) -> NatsSettings:
    return integration_runtime.nats_settings


@pytest.fixture(scope="session")
def redis_settings(integration_runtime: IntegrationRuntime) -> RedisSettings:
    return integration_runtime.redis_settings


@pytest.fixture
async def pg_connection(postgres_settings: PostgresSettings) -> AsyncGenerator:
    conn = await psycopg.AsyncConnection.connect(postgres_settings.url, row_factory=dict_row)
    try:
        await conn.execute("TRUNCATE users_outbox, users_versions, users_passwords, users RESTART IDENTITY CASCADE")
        await conn.commit()
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def redis_client(redis_settings: RedisSettings) -> AsyncGenerator[Redis, None]:
    client = Redis.from_url(redis_settings.url, decode_responses=True)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest.fixture
def user_factory():
    def factory(email: str = "user@example.com"):
        return UserFactory.new(user_id=UserID(uuid7()), email=Email(email))

    return factory
