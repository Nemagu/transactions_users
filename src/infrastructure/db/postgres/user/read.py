from typing import Any
from uuid import uuid7

from psycopg.sql import SQL, Composed, Identifier

from application.dto.paginators import LimitOffsetPaginator
from application.ports.repositories.user import UserReadRepository
from domain.user import Email, User, UserFactory, UserID, UserState, UserStatus
from infrastructure.db.postgres.base import (
    BasePostgresRepository,
    handle_domain_errors,
)


class PostgresUserReadRepository(BasePostgresRepository, UserReadRepository):
    async def next_id(self) -> UserID:
        """Возвращает новый идентификатор пользователя."""
        return UserID(uuid7())

    async def by_id(self, user_id: UserID) -> User | None:
        """Возвращает пользователя по идентификатору."""
        query = SQL(
            """
            SELECT user_id, email, status, state, version
            FROM {}
            WHERE user_id = %s
            """
        ).format(Identifier(self._users_tables.read))
        row = await self._fetchone(query, (user_id.user_id,))
        if row is None:
            return None
        return self._model_to_domain(row)

    async def by_email(self, email: Email) -> User | None:
        """Возвращает пользователя по email."""
        query = SQL(
            """
            SELECT user_id, email, status, state, version
            FROM {}
            WHERE email = %s
            """
        ).format(Identifier(self._users_tables.read))
        row = await self._fetchone(query, (email.email,))
        if row is None:
            return None
        return self._model_to_domain(row)

    async def filters(
        self,
        paginator: LimitOffsetPaginator,
        user_ids: list[UserID] | None = None,
        statuses: list[UserStatus] | None = None,
        states: list[UserState] | None = None,
    ) -> tuple[list[User], int]:
        """Возвращает пользователей по фильтрам с пагинацией."""
        conditions, params = self._build_filter_conditions(user_ids, statuses, states)
        count = await self._count_rows(conditions, list(params), self._users_tables.read)
        if count == 0:
            return [], 0
        rows = await self._fetch_users_filtered(conditions, list(params), paginator)
        return [self._model_to_domain(row) for row in rows], count

    async def save(self, user: User) -> None:
        """Сохраняет пользователя с учетом версии агрегата."""
        if user.version.version == 1:
            await self._create(user)
        else:
            await self._update(user)
        user.mark_persisted()

    def _build_filter_conditions(
        self,
        user_ids: list[UserID] | None,
        statuses: list[UserStatus] | None,
        states: list[UserState] | None,
    ) -> tuple[SQL | Composed, list[Any]]:
        conditions = [SQL("WHERE 1 = 1")]
        params: list[Any] = []
        if user_ids is not None:
            conditions.append(SQL("user_id = ANY(%s)"))
            params.append([uid.user_id for uid in user_ids])
        if statuses is not None:
            conditions.append(SQL("status = ANY(%s)"))
            params.append([s.value for s in statuses])
        if states is not None:
            conditions.append(SQL("state = ANY(%s)"))
            params.append([s.value for s in states])
        return SQL(" AND ").join(conditions), params

    async def _fetch_users_filtered(
        self,
        conditions: SQL | Composed,
        params: list[Any],
        paginator: LimitOffsetPaginator,
    ) -> list:
        base = SQL("SELECT user_id, email, status, state, version FROM {}").format(
            Identifier(self._users_tables.read)
        )
        query, all_params = self._extend_query_with_limit_offset(
            base, conditions, params, paginator, order_by=SQL("user_id")
        )
        return await self._fetchall(query, all_params)

    async def _create(self, user: User) -> None:
        query = SQL(
            """
            INSERT INTO {} (user_id, email, status, state, version)
            VALUES (%s, %s, %s, %s, %s)
            """
        ).format(Identifier(self._users_tables.read))
        await self._execute(
            query,
            (
                user.user_id.user_id,
                user.email.email,
                user.status.value,
                user.state.value,
                user.version.version,
            ),
        )

    async def _update(self, user: User) -> None:
        query = SQL(
            """
            UPDATE {}
            SET email = %s,
                status = %s,
                state = %s,
                version = %s
            WHERE user_id = %s
            """
        ).format(Identifier(self._users_tables.read))
        await self._execute(
            query,
            (
                user.email.email,
                user.status.value,
                user.state.value,
                user.version.version,
                user.user_id.user_id,
            ),
        )

    @handle_domain_errors
    def _model_to_domain(self, row: dict) -> User:
        return UserFactory.restore(
            user_id=row["user_id"],
            email=row["email"],
            status=row["status"],
            state=row["state"],
            version=row["version"],
        )
