from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from infrastructure.config import APIWorkerSettings
from presentation.api.server import APIWorker


@pytest.fixture(scope="session")
def api_config_file(
    integration_runtime,
    tmp_path_factory,
) -> Path:
    directory = tmp_path_factory.mktemp("presentation_api")
    private_key = directory / "private.pem"
    public_key = directory / "public.pem"
    config_file = directory / "api_worker.yaml"

    private_key.write_text("PRIVATE_KEY", encoding="utf-8")
    public_key.write_text("PUBLIC_KEY", encoding="utf-8")

    config_file.write_text(
        f"""logging:
  level: info

fastapi:
  user_id_header_name: x-user-id
  request_id_header_name: x-request-id
  process_time_header_name: x-process-time
  process_time_ms_header_name: x-process-time-ms

uvicorn:
  host: 127.0.0.1
  port: 8000
  workers: 1
  reload: false
  loop: uvloop

nats:
  host: 127.0.0.1
  port: {integration_runtime.nats_port}
  healthcheck_file: /tmp/nats_worker_healthbeat
  loop_sleep_duration: 1
  connect_name: users_api_tests
  reconnect_time_wait: 1
  connect_timeout: 5
  ping_interval: 120
  max_outstanding_pings: 3
  email:
    stream_name: email
    send_subject_name: send

db:
  host: 127.0.0.1
  port: {integration_runtime.postgres_port}
  user: users
  database: users
  password_file: {integration_runtime.postgres_password_file}
  pool:
    min_size: 1
    max_size: 5
    max_inactive_connection_lifetime: 60
    max_connection_lifetime: 300
    timeout: 10

redis:
  host: 127.0.0.1
  port: {integration_runtime.redis_port}
  db: 0
  password: null
  decode_responses: true
  healthcheck_interval: 30
  socket_timeout: 5
  socket_connect_timeout: 5

jwt:
  algorithm: RS256
  private_key_file: {private_key}
  public_key_file: {public_key}
  issuer: users
  audience: users_api
  access_token_ttl_seconds: 900
  refresh_token_ttl_seconds: 2592000
  leeway_seconds: 0
""",
        encoding="utf-8",
    )
    return config_file


@pytest.fixture(scope="session")
def api_settings(api_config_file: Path) -> Generator[APIWorkerSettings, None, None]:
    import os

    prev = os.environ.get("CONFIG_FILE")
    os.environ["CONFIG_FILE"] = str(api_config_file)
    try:
        yield APIWorkerSettings()
    finally:
        if prev is None:
            os.environ.pop("CONFIG_FILE", None)
        else:
            os.environ["CONFIG_FILE"] = prev


@pytest_asyncio.fixture
async def api_client(api_settings: APIWorkerSettings) -> AsyncGenerator[AsyncClient, None]:
    app = APIWorker(api_settings).app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with app.router.lifespan_context(app):
            yield client
