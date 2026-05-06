from collections.abc import Callable
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from application.dto.paginators import LimitOffsetPaginator
from application.dto.user import UserSimpleDTO, UserVersionSimpleDTO
from application.errors import AppInvalidDataError
from application.queries.public.user.list_last_versions import (
    UserLastVersionsQuery,
    UserLastVersionsUseCase,
)
from application.queries.public.user.list_versions import UserVersionsQuery, UserVersionsUseCase
from application.queries.public.user.retrieve_last_version import (
    UserLastVersionQuery,
    UserLastVersionUseCase,
)
from application.queries.public.user.retrieve_version import UserVersionQuery, UserVersionUseCase
from domain.errors import EntityPolicyError
from domain.user.value_objects import UserStatus

_PAGINATOR = LimitOffsetPaginator()


class _FakeUow:
    def __init__(
        self,
        *,
        by_id=None,
        read_filters: tuple = ([], 0),
        version_by_id=None,
        version_filters: tuple = ([], 0),
    ) -> None:
        _by_id = by_id
        _read_filters = read_filters
        _version_by_id = version_by_id
        _version_filters = version_filters

        async def _read_by_id(user_id):
            return _by_id(user_id) if callable(_by_id) else _by_id

        async def _read_filters_fn(**kwargs):
            return _read_filters

        async def _ver_by_id(user_id, version):
            return _version_by_id(user_id, version) if callable(_version_by_id) else _version_by_id

        async def _ver_filters(**kwargs):
            return _version_filters

        self.user_repositories = SimpleNamespace(
            read=SimpleNamespace(by_id=_read_by_id, filters=_read_filters_fn),
            version=SimpleNamespace(by_id_version=_ver_by_id, filters=_ver_filters),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.parametrize(
    ("use_case_class", "query_factory"),
    [
        (
            UserLastVersionUseCase,
            lambda uid: UserLastVersionQuery(initiator_id=uid, user_id=uid),
        ),
        (
            UserVersionUseCase,
            lambda uid: UserVersionQuery(initiator_id=uid, user_id=uid, version=1),
        ),
        (
            UserLastVersionsUseCase,
            lambda uid: UserLastVersionsQuery(
                initiator_id=uid, paginator=_PAGINATOR, user_ids=[uid], statuses=None, states=None
            ),
        ),
        (
            UserVersionsUseCase,
            lambda uid: UserVersionsQuery(
                initiator_id=uid,
                user_id=uid,
                paginator=_PAGINATOR,
                statuses=None,
                states=None,
                from_version=None,
                to_version=None,
            ),
        ),
    ],
    ids=["retrieve_last", "retrieve_version", "list_last", "list_versions"],
)
async def test_initiator_not_found_raises(
    use_case_class, query_factory: Callable[[UUID], object]
):
    uow = _FakeUow(by_id=None)
    with pytest.raises(AppInvalidDataError):
        await use_case_class(uow).execute(query_factory(uuid4()))


async def test_last_version_self_access_returns_dto(user_factory):
    user = user_factory()
    uow = _FakeUow(by_id=user)
    query = UserLastVersionQuery(initiator_id=user.user_id.user_id, user_id=user.user_id.user_id)
    dto = await UserLastVersionUseCase(uow).execute(query)
    assert isinstance(dto, UserSimpleDTO)
    assert dto.user_id == user.user_id.user_id


async def test_last_version_admin_access_returns_target_dto(user_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    target = user_factory()
    uow = _FakeUow(by_id=lambda uid: initiator if uid == initiator.user_id else target)
    query = UserLastVersionQuery(
        initiator_id=initiator.user_id.user_id, user_id=target.user_id.user_id
    )
    dto = await UserLastVersionUseCase(uow).execute(query)
    assert dto.user_id == target.user_id.user_id


async def test_last_version_non_admin_access_other_raises(user_factory):
    initiator = user_factory(status=UserStatus.USER)
    target = user_factory()
    uow = _FakeUow(by_id=lambda uid: initiator if uid == initiator.user_id else target)
    query = UserLastVersionQuery(
        initiator_id=initiator.user_id.user_id, user_id=target.user_id.user_id
    )
    with pytest.raises(EntityPolicyError):
        await UserLastVersionUseCase(uow).execute(query)


async def test_last_version_target_not_found_raises(user_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    uow = _FakeUow(by_id=lambda uid: initiator if uid == initiator.user_id else None)
    query = UserLastVersionQuery(
        initiator_id=initiator.user_id.user_id, user_id=uuid4()
    )
    with pytest.raises(AppInvalidDataError):
        await UserLastVersionUseCase(uow).execute(query)


async def test_version_self_access_returns_dto(user_factory, user_version_dto_factory):
    user = user_factory()
    version_dto = user_version_dto_factory()
    uow = _FakeUow(by_id=user, version_by_id=version_dto)
    query = UserVersionQuery(
        initiator_id=user.user_id.user_id, user_id=user.user_id.user_id, version=1
    )
    dto = await UserVersionUseCase(uow).execute(query)
    assert isinstance(dto, UserVersionSimpleDTO)


async def test_version_admin_access_returns_dto(user_factory, user_version_dto_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    version_dto = user_version_dto_factory()
    uow = _FakeUow(by_id=initiator, version_by_id=version_dto)
    query = UserVersionQuery(
        initiator_id=initiator.user_id.user_id, user_id=uuid4(), version=1
    )
    dto = await UserVersionUseCase(uow).execute(query)
    assert isinstance(dto, UserVersionSimpleDTO)


async def test_version_non_admin_access_other_raises(user_factory):
    initiator = user_factory(status=UserStatus.USER)
    uow = _FakeUow(by_id=initiator)
    query = UserVersionQuery(
        initiator_id=initiator.user_id.user_id, user_id=uuid4(), version=1
    )
    with pytest.raises(EntityPolicyError):
        await UserVersionUseCase(uow).execute(query)


async def test_version_not_found_raises(user_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    uow = _FakeUow(by_id=initiator, version_by_id=None)
    query = UserVersionQuery(
        initiator_id=initiator.user_id.user_id, user_id=uuid4(), version=99
    )
    with pytest.raises(AppInvalidDataError):
        await UserVersionUseCase(uow).execute(query)


async def test_last_versions_self_only_returns_results(user_factory):
    user = user_factory()
    uow = _FakeUow(by_id=user, read_filters=([user], 1))
    query = UserLastVersionsQuery(
        initiator_id=user.user_id.user_id,
        paginator=_PAGINATOR,
        user_ids=[user.user_id.user_id],
        statuses=None,
        states=None,
    )
    result, count = await UserLastVersionsUseCase(uow).execute(query)
    assert count == 1
    assert result[0].user_id == user.user_id.user_id


async def test_last_versions_admin_returns_results(user_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    other = user_factory()
    uow = _FakeUow(by_id=initiator, read_filters=([initiator, other], 2))
    query = UserLastVersionsQuery(
        initiator_id=initiator.user_id.user_id,
        paginator=_PAGINATOR,
        user_ids=None,
        statuses=None,
        states=None,
    )
    result, count = await UserLastVersionsUseCase(uow).execute(query)
    assert count == 2
    assert len(result) == 2


async def test_last_versions_non_admin_without_self_filter_raises(user_factory):
    initiator = user_factory(status=UserStatus.USER)
    uow = _FakeUow(by_id=initiator)
    query = UserLastVersionsQuery(
        initiator_id=initiator.user_id.user_id,
        paginator=_PAGINATOR,
        user_ids=None,
        statuses=None,
        states=None,
    )
    with pytest.raises(EntityPolicyError):
        await UserLastVersionsUseCase(uow).execute(query)


async def test_versions_self_access_returns_results(user_factory, user_version_dto_factory):
    user = user_factory()
    version_dto = user_version_dto_factory()
    uow = _FakeUow(by_id=user, version_filters=([version_dto], 1))
    query = UserVersionsQuery(
        initiator_id=user.user_id.user_id,
        user_id=user.user_id.user_id,
        paginator=_PAGINATOR,
        statuses=None,
        states=None,
        from_version=None,
        to_version=None,
    )
    result, count = await UserVersionsUseCase(uow).execute(query)
    assert count == 1
    assert isinstance(result[0], UserVersionSimpleDTO)


async def test_versions_admin_access_returns_results(user_factory, user_version_dto_factory):
    initiator = user_factory(status=UserStatus.ADMIN)
    version_dto = user_version_dto_factory()
    uow = _FakeUow(by_id=initiator, version_filters=([version_dto], 1))
    query = UserVersionsQuery(
        initiator_id=initiator.user_id.user_id,
        user_id=uuid4(),
        paginator=_PAGINATOR,
        statuses=None,
        states=None,
        from_version=None,
        to_version=None,
    )
    result, count = await UserVersionsUseCase(uow).execute(query)
    assert count == 1


async def test_versions_non_admin_access_other_raises(user_factory):
    initiator = user_factory(status=UserStatus.USER)
    uow = _FakeUow(by_id=initiator)
    query = UserVersionsQuery(
        initiator_id=initiator.user_id.user_id,
        user_id=uuid4(),
        paginator=_PAGINATOR,
        statuses=None,
        states=None,
        from_version=None,
        to_version=None,
    )
    with pytest.raises(EntityPolicyError):
        await UserVersionsUseCase(uow).execute(query)
