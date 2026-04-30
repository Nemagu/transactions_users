from types import SimpleNamespace
from uuid import uuid4

import pytest

from application.command.base import BaseUseCase
from application.errors import AppInvalidDataError
from domain.user import UserID


class _TestUseCase(BaseUseCase):
    pass


@pytest.mark.asyncio
async def test_initiator_returns_user(user_factory):
    user = user_factory(user_id=uuid4())
    uow = SimpleNamespace(
        user_repositories=SimpleNamespace(
            read=SimpleNamespace(by_id=lambda _: user),
        )
    )

    async def by_id(_: UserID):
        return user

    uow.user_repositories.read.by_id = by_id
    got = await _TestUseCase(uow)._initiator(uow, user.user_id, "test action")

    assert got is user


@pytest.mark.asyncio
async def test_initiator_raises_if_user_not_found():
    async def by_id(_: UserID):
        return None

    uow = SimpleNamespace(
        user_repositories=SimpleNamespace(read=SimpleNamespace(by_id=by_id))
    )
    user_id = UserID(uuid4())

    with pytest.raises(AppInvalidDataError) as exc_info:
        await _TestUseCase(uow)._initiator(uow, user_id, "test action")

    assert exc_info.value.action == "test action"
    assert exc_info.value.data == {"user": {"user_id": user_id.user_id}}
