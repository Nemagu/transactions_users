from collections.abc import Callable

import pytest

from domain.errors import EntityAlreadyExistsError
from domain.user.entity import User
from domain.user.services import UserUniquenessService
from domain.user.value_objects import Email


class FakeUserReadRepository:
    def __init__(self, user: User | None) -> None:
        self._user = user

    async def by_email(self, email: Email) -> User | None:
        return self._user


@pytest.mark.asyncio
async def test_validate_email_passes_when_user_absent() -> None:
    service = UserUniquenessService(read_repository=FakeUserReadRepository(user=None))

    await service.validate_email(Email("new@example.com"))


@pytest.mark.asyncio
async def test_validate_email_raises_when_user_exists(
    user_factory: Callable[..., User],
) -> None:
    existing_user = user_factory(email="taken@example.com")
    service = UserUniquenessService(
        read_repository=FakeUserReadRepository(user=existing_user)
    )

    with pytest.raises(EntityAlreadyExistsError):
        await service.validate_email(Email("taken@example.com"))
