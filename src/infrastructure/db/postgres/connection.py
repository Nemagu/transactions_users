from contextlib import asynccontextmanager

from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from application.errors import AppInternalError
from infrastructure.config import PostgresSettings


class PostgresConnectionManager:
    def __init__(self, db_settings: PostgresSettings) -> None:
        self._db_settings = db_settings
        self._pool: AsyncConnectionPool[AsyncConnection[DictRow]] | None = None

    async def init(self) -> None:
        try:
            self._pool = AsyncConnectionPool[AsyncConnection[DictRow]](
                conninfo=self._db_settings.url,
                min_size=self._db_settings.pool.min_size,
                max_size=self._db_settings.pool.max_size,
                max_idle=self._db_settings.pool.max_inactive_connection_lifetime,
                max_lifetime=self._db_settings.pool.max_connection_lifetime,
                timeout=self._db_settings.pool.timeout,
                kwargs={"autocommit": False, "row_factory": dict_row},
                open=False,
            )
            await self._pool.open()
        except BaseException as err:
            raise AppInternalError(
                msg=f"ошибка при инициализации пулла соединений: {err}",
                action="инициализация пула соединений postgres",
                wrap_error=err,
            )

    @asynccontextmanager
    async def connection(self):
        if self._pool is None:
            raise AppInternalError(
                msg="ConnectionManager не инициализирован",
                action="попытка получения подключения из пула postgres",
            )
        async with self._pool.connection() as conn:
            yield conn

    async def close(self):
        if self._pool is None:
            return
        try:
            await self._pool.close()
        except BaseException as err:
            raise AppInternalError(
                msg=f"ошибка при закрытии пулла соединений: {err}",
                action="попытка закрытия пула подключений postgres",
                wrap_error=err,
            )
