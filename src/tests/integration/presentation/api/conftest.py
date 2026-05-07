from collections.abc import AsyncGenerator, Callable, Generator
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from infrastructure.config import APIWorkerSettings
from infrastructure.jwt.pyjwt import PyJWTManager
from presentation.api.server import APIWorker

_TEST_PRIVATE_KEY = """\
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAtUHtsnVrsr+XTOlK2sfuTJu83j3I3/zvMxypn1B0CV3A/Wdw
1Dc3GsrcDmotpKdfSyXBA7FsnPyt2+be+Cb+2E6DC7uzsRvPbEhzXjoryB0dh6pj
hxkjC5qVUZZwsiGksWWftQAMsUmrhQerMOz8yrFcBfoA/PmfqcWHY8MDobHtpob1
nQtMhq1OJigmd5+c6y1jFOSZy8WaSPb08sxy8CJKZ4bKWDFBrRk2i1EpPZ4wKoOo
8su5rb22age6CZ7ecQtnu2vI4dYnRZXaVoJrFWDMGiVLrPHHLwR56+C5emH9Wlj1
rMUD1hBSqi/Wyp+W8H5BTB7T8SZOg+d5a/gQyQIDAQABAoIBAADUIreFJXG/OC2g
rsvFacLLIVLqeT3HXqIfHB3ffoSemQfPi/Ie4x39jDM7Ic5w+g/cHo6gJlWpF0yK
6gwK/8AIo9q7fkGoy7wydTZpc/o/2HEZpSoR820kYp/CBItDUhy9M1pBLWs3TgFc
Ok6rB+0jJVzJUx5yfqDowoEBGcX+7H1Pn7gdrdFVB6i3AIOsk7RhNzVysTjlLXWA
OU3y1RZ7CSKQBcKMsho+KMIQsmeMj7OK+jtHy9axxcVDTPw4T7BtQ/nkVTiLkHlS
T17lgSy3rAHjK5403cUCK+Bt79jflPwRU7UfWb9FQ8EWQM14bJJGFjJ/JM1GwxuV
4tdM4nECgYEA9tYLzZ3JmeH88Ov0vhBTrXd2tWzgokJL4J9lnGcKVDt5JMpS6OzZ
LZFdyUzIP40IKIAHYM3VPiclhICzjr5SATYdP5PFzG3yMYsOs3ftMYGvWW0csiZ6
kxsjHYiNhMitgiZSvh3Fd9KEARG48fs/Zhrv2aqh5mosLF999B+KMSUCgYEAu/ye
B9EbG6muy1aOHC0NPQt5xiFtzbGe4tF4mjCLzL3jYRwuR/zdZ157in9Yd2FqkZmb
CWtUslDVtf0uwbBUXmgwIR6C7IUYyWVV26J8MEBaZl4TvEzvw5jknSPL526Puw8V
VCjPvp4O5MhfMhOJTJDFaKTgk0GMoqqxt4zxadUCgYEA4utqVG//e1l3aKDzEZv+
4VUXK7jZVjHugaToC/3qT/+Q4lKiIAJFsg+Wkc3ltg7YdislHUh9BrOEWSjcaZjr
2LM/9kfKqqJU6lj1feX9h+q6IlMd82VOgFiNUsRLncvDPwguPxstg3dj5Xu+c69P
3HVdFNU6G5J146EyMLCiIYUCgYEAlCFZfZtemwu4eu43iShO+D1ktaV92soOA3lA
aW+7mZg/5jPInF07McsX2mjCkz+mNBkwO9nhoalk3cUl5OZHdSTwWAis7idrArfh
UfLVnUf4dBXJw2V0wVJnQxQEBtfuVl5qVijamr/9yHXD3bfbRwQFKpJRjHfok/2h
kJt1WAkCgYBtbp/zfsMABOncskuYCA85sAL8dLLKYwDks22xDTVZreiyLeMdThVn
JESodfhke6nQ055yRiFP5gslceSYW8nru7INtV/dYkBx0Ylc74uvKkhjHa0MGr/l
jPonSwkDrIqfg9bM9hRJRSAW5YPHBhx11Am8vRuCsJ+An1Qy8gETcw==
-----END RSA PRIVATE KEY-----
"""

_TEST_PUBLIC_KEY = """\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtUHtsnVrsr+XTOlK2sfu
TJu83j3I3/zvMxypn1B0CV3A/Wdw1Dc3GsrcDmotpKdfSyXBA7FsnPyt2+be+Cb+
2E6DC7uzsRvPbEhzXjoryB0dh6pjhxkjC5qVUZZwsiGksWWftQAMsUmrhQerMOz8
yrFcBfoA/PmfqcWHY8MDobHtpob1nQtMhq1OJigmd5+c6y1jFOSZy8WaSPb08sxy
8CJKZ4bKWDFBrRk2i1EpPZ4wKoOo8su5rb22age6CZ7ecQtnu2vI4dYnRZXaVoJr
FWDMGiVLrPHHLwR56+C5emH9Wlj1rMUD1hBSqi/Wyp+W8H5BTB7T8SZOg+d5a/gQ
yQIDAQAB
-----END PUBLIC KEY-----
"""


@pytest.fixture(scope="session")
def api_config_file(
    integration_runtime,
    tmp_path_factory,
) -> Path:
    directory = tmp_path_factory.mktemp("presentation_api")
    private_key = directory / "private.pem"
    public_key = directory / "public.pem"
    config_file = directory / "api_worker.yaml"

    private_key.write_text(_TEST_PRIVATE_KEY, encoding="utf-8")
    public_key.write_text(_TEST_PUBLIC_KEY, encoding="utf-8")

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
  user: atlas_users
  database: atlas_users
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
  issuer: atlas_users
  audience: atlas_users_api
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


@pytest.fixture(scope="session")
def jwt_access_token(api_settings: APIWorkerSettings) -> Callable[[UUID], str]:
    """Возвращает фабрику access JWT-токенов для тестовых запросов."""
    manager = PyJWTManager(api_settings.jwt)
    return manager.issue_access_token


@pytest_asyncio.fixture
async def api_client(api_settings: APIWorkerSettings) -> AsyncGenerator[AsyncClient, None]:
    app = APIWorker(api_settings).app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with app.router.lifespan_context(app):
            yield client
