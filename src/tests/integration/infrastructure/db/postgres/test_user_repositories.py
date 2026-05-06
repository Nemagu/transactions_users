import pytest

from application.dto.paginators import LimitOffsetPaginator
from application.ports.repositories import UserEvent
from domain.user import Email
from domain.value_objects import Version
from infrastructure.db.postgres.user.outbox import PostgresUserOutboxRepository
from infrastructure.db.postgres.user.read import PostgresUserReadRepository
from infrastructure.db.postgres.user.version import PostgresUserVersionRepository

_PAGINATOR = LimitOffsetPaginator()


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
async def test_read_filters_returns_users_with_count(pg_connection, user_factory) -> None:
    repo = PostgresUserReadRepository(pg_connection)
    user_a = user_factory("filter_a@example.com")
    user_b = user_factory("filter_b@example.com")
    await repo.save(user_a)
    await repo.save(user_b)
    await pg_connection.commit()

    users, count = await repo.filters(_PAGINATOR)

    assert count == 2
    assert len(users) == 2


@pytest.mark.asyncio
async def test_read_filters_by_user_ids_returns_matching(pg_connection, user_factory) -> None:
    repo = PostgresUserReadRepository(pg_connection)
    user_a = user_factory("ids_a@example.com")
    user_b = user_factory("ids_b@example.com")
    await repo.save(user_a)
    await repo.save(user_b)
    await pg_connection.commit()

    users, count = await repo.filters(_PAGINATOR, user_ids=[user_a.user_id])

    assert count == 1
    assert users[0].user_id == user_a.user_id


@pytest.mark.asyncio
async def test_read_filters_returns_empty_when_no_match(pg_connection, user_factory) -> None:
    repo = PostgresUserReadRepository(pg_connection)
    user = user_factory("nomatch@example.com")
    await repo.save(user)
    await pg_connection.commit()

    users, count = await repo.filters(_PAGINATOR, user_ids=[user_factory("other@example.com").user_id])

    assert count == 0
    assert users == []


@pytest.mark.asyncio
async def test_version_by_id_version_returns_dto_when_found(pg_connection, user_factory) -> None:
    read_repo = PostgresUserReadRepository(pg_connection)
    version_repo = PostgresUserVersionRepository(pg_connection)
    user = user_factory("byver@example.com")
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.CREATED, editor_id=None)
    await pg_connection.commit()

    dto = await version_repo.by_id_version(user.user_id, user.version)

    assert dto is not None
    assert dto.user.user_id == user.user_id
    assert dto.event == UserEvent.CREATED


@pytest.mark.asyncio
async def test_version_by_id_version_returns_none_when_not_found(pg_connection, user_factory) -> None:
    read_repo = PostgresUserReadRepository(pg_connection)
    version_repo = PostgresUserVersionRepository(pg_connection)
    user = user_factory("byver_miss@example.com")
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.CREATED, editor_id=None)
    await pg_connection.commit()

    dto = await version_repo.by_id_version(user.user_id, Version(99))

    assert dto is None


@pytest.mark.asyncio
async def test_version_filters_returns_versions_with_count(pg_connection, user_factory) -> None:
    read_repo = PostgresUserReadRepository(pg_connection)
    version_repo = PostgresUserVersionRepository(pg_connection)
    user = user_factory("vfilter@example.com")
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.CREATED, editor_id=None)
    user.new_email(Email("vfilter2@example.com"))
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.UPDATED, editor_id=None)
    await pg_connection.commit()

    versions, count = await version_repo.filters(_PAGINATOR, user_id=user.user_id)

    assert count == 2
    assert len(versions) == 2


@pytest.mark.asyncio
async def test_version_filters_by_version_range(pg_connection, user_factory) -> None:
    read_repo = PostgresUserReadRepository(pg_connection)
    version_repo = PostgresUserVersionRepository(pg_connection)
    user = user_factory("vrange@example.com")
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.CREATED, editor_id=None)
    user.new_email(Email("vrange2@example.com"))
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.UPDATED, editor_id=None)
    user.new_email(Email("vrange3@example.com"))
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.UPDATED, editor_id=None)
    await pg_connection.commit()

    versions, count = await version_repo.filters(
        _PAGINATOR, user_id=user.user_id, from_version=Version(2), to_version=Version(3)
    )

    assert count == 2
    assert all(2 <= v.user.version.version <= 3 for v in versions)


@pytest.mark.asyncio
async def test_version_filters_returns_empty_when_no_match(pg_connection, user_factory) -> None:
    read_repo = PostgresUserReadRepository(pg_connection)
    version_repo = PostgresUserVersionRepository(pg_connection)
    user = user_factory("vnomatch@example.com")
    await read_repo.save(user)
    await version_repo.save(user=user, event=UserEvent.CREATED, editor_id=None)
    await pg_connection.commit()

    versions, count = await version_repo.filters(
        _PAGINATOR, user_id=user.user_id, from_version=Version(99)
    )

    assert count == 0
    assert versions == []


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
