from uuid import uuid7

from psycopg.sql import SQL, Identifier

from application.ports.repositories.user import UserReadRepository
from domain.user import Email, User, UserFactory, UserID
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

    async def save(self, user: User) -> None:
        """Сохраняет пользователя с учетом версии агрегата."""
        if user.version.version == 1:
            await self._create(user)
        else:
            await self._update(user)
        user.mark_persisted()

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
