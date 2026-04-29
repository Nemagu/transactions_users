from psycopg.sql import SQL, Identifier

from application.ports.repositories.password import UserPasswordRepository
from domain.user import User, UserID
from infrastructure.db.postgres.base import BasePostgresRepository


class PostgresUserPasswordRepository(BasePostgresRepository, UserPasswordRepository):
    async def by_user_id(self, user_id: UserID) -> str | None:
        """Возвращает хеш пароля пользователя."""
        query = SQL(
            """
            SELECT password_hash
            FROM {}
            WHERE user_id = %s
            """
        ).format(Identifier(self._users_passwords_table))
        row = await self._fetchone(query, (user_id.user_id,))
        if row is None:
            return None
        return row["password_hash"]

    async def save(self, user: User, hashed_password: str) -> None:
        """Сохраняет хеш пароля пользователя."""
        query = SQL(
            """
            INSERT INTO {} (password_hash, user_id)
            VALUES (%s, %s)
            """
        ).format(Identifier(self._users_passwords_table))
        await self._execute(query, (hashed_password, user.user_id.user_id))
