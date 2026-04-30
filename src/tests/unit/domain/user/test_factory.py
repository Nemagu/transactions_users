from uuid import uuid4

from domain.user.entity import User
from domain.user.factory import UserFactory
from domain.user.value_objects import Email, UserID, UserState, UserStatus


def test_new_creates_default_user() -> None:
    user = UserFactory.new(user_id=UserID(uuid4()), email=Email("u@example.com"))

    assert user.status == UserStatus.USER
    assert user.state == UserState.ACTIVE
    assert user.version.version == 1


def test_restore_builds_user_from_primitives() -> None:
    user_id = uuid4()

    user = UserFactory.restore(
        user_id=user_id,
        email="admin@example.com",
        status="admin",
        state="frozen",
        version=7,
    )

    assert isinstance(user, User)
    assert user.user_id.user_id == user_id
    assert user.email.email == "admin@example.com"
    assert user.status == UserStatus.ADMIN
    assert user.state == UserState.FROZEN
    assert user.version.version == 7
