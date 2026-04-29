from abc import ABC
from dataclasses import dataclass
from functools import wraps
from typing import Any, Iterable, LiteralString
from uuid import UUID

from psycopg import AsyncConnection, Error
from psycopg.rows import DictRow
from psycopg.sql import SQL, Composed, Identifier

from application.dto.paginators import LimitOffsetPaginator
from application.errors import AppInternalError
from domain.errors import DomainError


def handle_db_errors(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Error as e:
            raise AppInternalError(
                msg=str(e), action="взаимодействие с базой данных", wrap_error=e
            ) from e

    return wrapper


def handle_domain_errors(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except DomainError as e:
            raise AppInternalError(
                msg=str(e), action=e.struct_name, data=e.data, wrap_error=e
            ) from e

    return wrapper


@dataclass
class PrivateAggregateTables:
    read: str
    version: str


@dataclass
class PublicAggregateTables(PrivateAggregateTables):
    outbox: str


class BasePostgresRepository(ABC):
    _transactions_users_tables = "transactions_users_tables"
    _users_passwords_table = "users_passwords"
    _users_tables = PublicAggregateTables("users", "users_versions", "users_outbox")

    def __init__(self, conn: AsyncConnection[DictRow]):
        self._conn = conn

    @handle_db_errors
    async def _execute(
        self,
        query: bytes | LiteralString | SQL | Composed,
        params: tuple | None = None,
    ) -> None:
        async with self._conn.cursor() as cur:
            await cur.execute(query, params)

    @handle_db_errors
    async def _executemany(
        self,
        query: bytes | LiteralString | SQL | Composed,
        params_seq: Iterable[tuple],
    ) -> None:
        async with self._conn.cursor() as cur:
            await cur.executemany(query, params_seq)

    @handle_db_errors
    async def _fetchone(
        self,
        query: bytes | LiteralString | SQL | Composed,
        params: tuple | None = None,
    ) -> DictRow | None:
        async with self._conn.cursor() as cur:
            await cur.execute(query, params)
            return await cur.fetchone()

    @handle_db_errors
    async def _fetchall(
        self,
        query: bytes | LiteralString | SQL | Composed,
        params: tuple | None = None,
    ) -> list[DictRow]:
        async with self._conn.cursor() as cur:
            await cur.execute(query, params)
            return await cur.fetchall()

    async def _count_rows(
        self, conditions: SQL | Composed, params: list[Any], table_name: str
    ) -> int:
        count_query = SQL(
            """
            SELECT COUNT(*) AS count_rows
            FROM {}
            """
        ).format(Identifier(table_name))
        count_query = SQL(" ").join((count_query, conditions))
        count = await self._fetchone(count_query, tuple(params))
        if count is None:
            return 0
        else:
            return count["count_rows"]

    async def _source_table_id(self, table_name: str) -> UUID:
        query = SQL(
            """
            SELECT id
            FROM {}
            WHERE name = %s
            """
        ).format(Identifier(self._transactions_users_tables))
        row = await self._fetchone(query, (table_name,))
        if row is None:
            raise AppInternalError(
                msg="не удалось определить source_table_id для employees",
                action="получение source_table_id подписок участника",
                data={"table_name": table_name},
            )
        return row["id"]

    def _extend_query_with_limit_offset(
        self,
        query: SQL | Composed,
        conditions: SQL | Composed,
        params: list[Any],
        paginator: LimitOffsetPaginator,
        order_by: SQL | Composed = SQL("version"),
    ) -> tuple[SQL | Composed, list[Any]]:
        query = SQL(" ").join(
            (query, conditions, SQL("ORDER BY"), order_by, SQL("LIMIT %s OFFSET %s"))
        )
        params.extend([paginator.limit, paginator.offset])
        return query, params
