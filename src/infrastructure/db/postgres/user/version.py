from typing import Any

from psycopg.sql import SQL, Composed, Identifier

from application.dto.paginators import LimitOffsetPaginator
from application.ports.repositories.user import (
    UserEvent,
    UserVersionDTO,
    UserVersionRepository,
)
from domain.user import User, UserFactory, UserID, UserState, UserStatus
from domain.value_objects import Version
from infrastructure.db.postgres.base import BasePostgresRepository, handle_domain_errors


class PostgresUserVersionRepository(BasePostgresRepository, UserVersionRepository):
    async def by_id_version(
        self, user_id: UserID, version: Version
    ) -> UserVersionDTO | None:
        """Возвращает версию пользователя по идентификатору и номеру версии."""
        query = SQL(
            """
            SELECT user_id, email, status, state, version, event, editor_id, created_at
            FROM {}
            WHERE user_id = %s AND version = %s
            """
        ).format(Identifier(self._users_tables.version))
        row = await self._fetchone(query, (user_id.user_id, version.version))
        if row is None:
            return None
        return self._model_to_domain(row)

    async def filters(
        self,
        paginator: LimitOffsetPaginator,
        user_id: UserID,
        statuses: list[UserStatus] | None = None,
        states: list[UserState] | None = None,
        from_version: Version | None = None,
        to_version: Version | None = None,
    ) -> tuple[list[UserVersionDTO], int]:
        """Возвращает версии пользователя по фильтрам с пагинацией."""
        conditions, params = self._build_filter_conditions(
            user_id, statuses, states, from_version, to_version
        )
        count = await self._count_rows(conditions, list(params), self._users_tables.version)
        if count == 0:
            return [], 0
        rows = await self._fetch_versions_filtered(conditions, list(params), paginator)
        return [self._model_to_domain(row) for row in rows], count

    async def save(self, user: User, event: UserEvent, editor_id: UserID | None) -> None:
        """Сохраняет событие версии пользователя."""
        await self.batch_save([(user, event, editor_id)])

    async def batch_save(
        self, users_events_editor_ids: list[tuple[User, UserEvent, UserID | None]]
    ) -> None:
        """Сохраняет пачку событий версий пользователей."""
        if not users_events_editor_ids:
            return
        query = """
            INSERT INTO users_versions (
                user_id,
                email,
                status,
                state,
                version,
                event,
                editor_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            (
                user.user_id.user_id,
                user.email.email,
                user.status.value,
                user.state.value,
                user.version.version,
                event.value,
                editor_id.user_id if editor_id is not None else None,
            )
            for user, event, editor_id in users_events_editor_ids
        ]
        await self._executemany(query, params)

    def _build_filter_conditions(
        self,
        user_id: UserID,
        statuses: list[UserStatus] | None,
        states: list[UserState] | None,
        from_version: Version | None,
        to_version: Version | None,
    ) -> tuple[SQL | Composed, list[Any]]:
        conditions = [SQL("WHERE user_id = %s")]
        params: list[Any] = [user_id.user_id]
        if statuses is not None:
            conditions.append(SQL("status = ANY(%s)"))
            params.append([s.value for s in statuses])
        if states is not None:
            conditions.append(SQL("state = ANY(%s)"))
            params.append([s.value for s in states])
        if from_version is not None:
            conditions.append(SQL("version >= %s"))
            params.append(from_version.version)
        if to_version is not None:
            conditions.append(SQL("version <= %s"))
            params.append(to_version.version)
        return SQL(" AND ").join(conditions), params

    async def _fetch_versions_filtered(
        self,
        conditions: SQL | Composed,
        params: list[Any],
        paginator: LimitOffsetPaginator,
    ) -> list:
        base = SQL(
            "SELECT user_id, email, status, state, version, event, editor_id, created_at FROM {}"
        ).format(Identifier(self._users_tables.version))
        query, all_params = self._extend_query_with_limit_offset(
            base, conditions, params, paginator, order_by=SQL("version")
        )
        return await self._fetchall(query, all_params)

    @handle_domain_errors
    def _model_to_domain(self, row: dict) -> UserVersionDTO:
        user = UserFactory.restore(
            user_id=row["user_id"],
            email=row["email"],
            status=row["status"],
            state=row["state"],
            version=row["version"],
        )
        editor_id = UserID(row["editor_id"]) if row["editor_id"] is not None else None
        return UserVersionDTO(
            user=user,
            event=UserEvent.from_str(row["event"]),
            editor_id=editor_id,
            created_at=row["created_at"],
        )
