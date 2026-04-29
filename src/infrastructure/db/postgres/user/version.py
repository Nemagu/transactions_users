from application.ports.repositories.user import UserEvent, UserVersionRepository
from domain.user import User, UserID
from infrastructure.db.postgres.base import BasePostgresRepository


class PostgresUserVersionRepository(BasePostgresRepository, UserVersionRepository):
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
