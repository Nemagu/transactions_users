from uuid import uuid7

import psycopg
import pytest

from application.ports.repositories import UserEvent
from domain.user import Email, UserFactory, UserID
from infrastructure.db.postgres.password import PostgresUserPasswordRepository
from infrastructure.db.postgres.unit_of_work import PostgresUnitOfWork


@pytest.mark.asyncio
async def test_password_repository_save_and_get(pg_connection) -> None:
    user = UserFactory.new(user_id=UserID(uuid7()), email=Email("pwd@example.com"))

    async with pg_connection.cursor() as cur:
        await cur.execute(
            "INSERT INTO users (user_id, email, status, state, version) VALUES (%s, %s, %s, %s, %s)",
            (
                user.user_id.user_id,
                user.email.email,
                user.status.value,
                user.state.value,
                user.version.version,
            ),
        )
    repo = PostgresUserPasswordRepository(pg_connection)

    await repo.save(user, "hash123")
    await pg_connection.commit()

    assert await repo.by_user_id(user.user_id) == "hash123"


@pytest.mark.asyncio
async def test_unit_of_work_commit_and_repositories(postgres_settings) -> None:
    conn = await psycopg.AsyncConnection.connect(postgres_settings.url)
    try:
        user = UserFactory.new(user_id=UserID(uuid7()), email=Email("uow@example.com"))
        async with PostgresUnitOfWork(conn) as uow:
            await uow.user_repositories.read.save(user)
            await uow.user_repositories.version.save(user, UserEvent.CREATED, None)
    finally:
        if not conn.closed:
            await conn.close()

    verify = await psycopg.AsyncConnection.connect(postgres_settings.url)
    try:
        async with verify.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (user.user_id.user_id,))
            row = await cur.fetchone()
        assert row[0] == 1
    finally:
        await verify.close()


@pytest.mark.asyncio
async def test_unit_of_work_rollback_on_error(postgres_settings) -> None:
    conn = await psycopg.AsyncConnection.connect(postgres_settings.url)
    user_id = UserID(uuid7())
    try:
        with pytest.raises(RuntimeError):
            async with PostgresUnitOfWork(conn) as uow:
                user = UserFactory.new(user_id=user_id, email=Email("rollback@example.com"))
                await uow.user_repositories.read.save(user)
                raise RuntimeError("force rollback")
    finally:
        if not conn.closed:
            await conn.close()

    verify = await psycopg.AsyncConnection.connect(postgres_settings.url)
    try:
        async with verify.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (user_id.user_id,))
            row = await cur.fetchone()
        assert row[0] == 0
    finally:
        await verify.close()
