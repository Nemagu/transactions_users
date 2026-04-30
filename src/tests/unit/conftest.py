from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from application.ports.repositories import UserEvent, UserVersionDTO
from domain.user.entity import User
from domain.user.value_objects import Email, UserID, UserState, UserStatus
from domain.value_objects import Version


@pytest.fixture
def user_factory() -> Callable[..., User]:
    def factory(
        *,
        user_id: UUID | None = None,
        email: str = "user@example.com",
        status: UserStatus = UserStatus.USER,
        state: UserState = UserState.ACTIVE,
        version: int = 1,
    ) -> User:
        return User(
            user_id=UserID(user_id or uuid4()),
            email=Email(email),
            status=status,
            state=state,
            version=Version(version),
        )

    return factory


@pytest.fixture
def user_version_dto_factory(
    user_factory: Callable[..., User],
) -> Callable[..., UserVersionDTO]:
    def factory(
        *,
        event: UserEvent = UserEvent.CREATED,
        editor_id: UserID | None = None,
        created_at: datetime | None = None,
    ) -> UserVersionDTO:
        return UserVersionDTO(
            user=user_factory(),
            event=event,
            editor_id=editor_id,
            created_at=created_at or datetime.now(tz=timezone.utc),
        )

    return factory
