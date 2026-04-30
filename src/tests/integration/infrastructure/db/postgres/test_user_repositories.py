import pytest

from application.ports.repositories import UserEvent
from domain.user import Email
from infrastructure.db.postgres.user.outbox import PostgresUserOutboxRepository
from infrastructure.db.postgres.user.read import PostgresUserReadRepository
from infrastructure.db.postgres.user.version import PostgresUserVersionRepository


@pytest.mark.asyncio
async def test_user_read_repository_save_and_load(pg_connection, user_factory) -> None:
    repo = PostgresUserReadRepository(pg_connection)
    user = user_factory("read@example.com")

    await repo.save(user)
    await pg_connection.commit()

    loaded_by_id = await repo.by_id(user.user_id)
    loaded_by_email = await repo.by_email(Email("read@example.com"))

    assert loaded_by_id is not None
    assert loaded_by_id.user_id == user.user_id
    assert loaded_by_email is not None
    assert loaded_by_email.email.email == "read@example.com"


@pytest.mark.asyncio
async def test_user_read_repository_updates_existing_user(pg_connection, user_factory) -> None:
    repo = PostgresUserReadRepository(pg_connection)
    user = user_factory("before@example.com")
    await repo.save(user)
    user.new_email(Email("after@example.com"))

    await repo.save(user)
    await pg_connection.commit()

    loaded = await repo.by_id(user.user_id)

    assert loaded is not None
    assert loaded.email.email == "after@example.com"
    assert loaded.version.version == 2


@pytest.mark.asyncio
async def test_user_version_and_outbox_repositories(pg_connection, user_factory) -> None:
    read_repo = PostgresUserReadRepository(pg_connection)
    version_repo = PostgresUserVersionRepository(pg_connection)
    outbox_repo = PostgresUserOutboxRepository(pg_connection)
    user = user_factory("events@example.com")

    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.CREATED, editor_id=None)

    not_published_before = await outbox_repo.not_published_versions()
    assert len(not_published_before) == 1
    assert not_published_before[0].event == UserEvent.CREATED

    await outbox_repo.save(user)
    await pg_connection.commit()

    not_published_after = await outbox_repo.not_published_versions()
    assert not not_published_after
