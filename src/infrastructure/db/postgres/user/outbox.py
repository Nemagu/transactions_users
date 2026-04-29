from application.ports.repositories.user import (
    UserEvent,
    UserOutboxRepository,
    UserVersionDTO,
)
from domain.user import User, UserFactory, UserID
from infrastructure.db.postgres.base import BasePostgresRepository, handle_domain_errors


class PostgresUserOutboxRepository(BasePostgresRepository, UserOutboxRepository):
    async def save(self, user: User) -> None:
        """Помечает версию пользователя как опубликованную."""
        await self.batch_save([user])

    async def batch_save(self, users: list[User]) -> None:
        """Помечает пачку версий пользователей как опубликованные."""
        if not users:
            return
        query = """
            INSERT INTO users_outbox (user_id, version)
            VALUES (%s, %s)
        """
        params = [(user.user_id.user_id, user.version.version) for user in users]
        await self._executemany(query, params)

    async def not_published_versions(self) -> list[UserVersionDTO]:
        """Возвращает непубликованные версии пользователей."""
        query = """
            SELECT v.user_id,
                   v.email,
                   v.status,
                   v.state,
                   v.version,
                   v.event,
                   v.editor_id,
                   v.created_at
            FROM users_versions AS v
            LEFT JOIN users_outbox AS o
              ON o.user_id = v.user_id
             AND o.version = v.version
            WHERE o.id IS NULL
            ORDER BY v.created_at, v.version
        """
        rows = await self._fetchall(query)
        return [self._model_to_domain(row) for row in rows]

    @handle_domain_errors
    def _model_to_domain(self, row: dict) -> UserVersionDTO:
        user = UserFactory.restore(
            user_id=row["user_id"],
            email=row["email"],
            status=row["status"],
            state=row["state"],
            version=row["version"],
        )
        return UserVersionDTO(
            user=user,
            event=UserEvent.from_str(row["event"]),
            editor_id=UserID(row["editor_id"]) if row["editor_id"] is not None else None,
            created_at=row["created_at"],
        )
