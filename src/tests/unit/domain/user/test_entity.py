from collections.abc import Callable

import pytest

from domain.errors import EntityIdempotentError, EntityPolicyError
from domain.user.entity import User
from domain.user.value_objects import Email, UserState, UserStatus


def test_new_email_updates_value_and_version(user_factory: Callable[..., User]) -> None:
    user = user_factory(version=1)

    user.new_email(Email("new@example.com"))

    assert user.email.email == "new@example.com"
    assert user.version.version == 2


def test_new_email_does_not_increment_version_twice_without_persist(
    user_factory: Callable[..., User],
) -> None:
    user = user_factory(version=1)

    user.new_email(Email("new1@example.com"))
    user.new_state(UserState.FROZEN)

    assert user.version.version == 2


def test_mark_persisted_allows_next_increment(user_factory: Callable[..., User]) -> None:
    user = user_factory(version=1)
    user.new_email(Email("new1@example.com"))
    user.mark_persisted()

    user.new_state(UserState.FROZEN)

    assert user.version.version == 3


@pytest.mark.parametrize(
    "method_name",
    ["appoint_admin", "appoint_user", "new_state", "activate", "freeze", "delete"],
    ids=["appoint-admin", "appoint-user", "new-state", "activate", "freeze", "delete"],
)
def test_idempotent_actions_raise_error(
    user_factory: Callable[..., User], method_name: str
) -> None:
    user = user_factory(status=UserStatus.ADMIN, state=UserState.ACTIVE)

    if method_name == "appoint_user":
        user = user_factory(status=UserStatus.USER)
    if method_name == "new_state":
        with pytest.raises(EntityIdempotentError):
            user.new_state(UserState.ACTIVE)
        return
    if method_name == "activate":
        with pytest.raises(EntityIdempotentError):
            user.activate()
        return
    if method_name == "freeze":
        user = user_factory(state=UserState.FROZEN)
    if method_name == "delete":
        user = user_factory(state=UserState.DELETED)

    with pytest.raises(EntityIdempotentError):
        getattr(user, method_name)()


@pytest.mark.parametrize(
    "state",
    [UserState.FROZEN, UserState.DELETED],
    ids=["frozen", "deleted"],
)
def test_new_email_restricted_for_frozen_or_deleted(
    user_factory: Callable[..., User], state: UserState
) -> None:
    user = user_factory(state=state)

    with pytest.raises(EntityPolicyError):
        user.new_email(Email("new@example.com"))


def test_staff_rejects_regular_user(user_factory: Callable[..., User]) -> None:
    user = user_factory(status=UserStatus.USER)

    with pytest.raises(EntityPolicyError):
        user.staff()


def test_staff_passes_for_admin(user_factory: Callable[..., User]) -> None:
    user = user_factory(status=UserStatus.ADMIN)

    user.staff()


def test_new_email_idempotent_raises(user_factory: Callable[..., User]) -> None:
    user = user_factory(email="same@example.com")

    with pytest.raises(EntityIdempotentError):
        user.new_email(Email("same@example.com"))


def test_appoint_admin_changes_status(user_factory: Callable[..., User]) -> None:
    user = user_factory(status=UserStatus.USER)

    user.appoint_admin()

    assert user.status == UserStatus.ADMIN
    assert user.version.version == 2


def test_appoint_user_changes_status(user_factory: Callable[..., User]) -> None:
    user = user_factory(status=UserStatus.ADMIN)

    user.appoint_user()

    assert user.status == UserStatus.USER
    assert user.version.version == 2


def test_activate_changes_state(user_factory: Callable[..., User]) -> None:
    user = user_factory(state=UserState.FROZEN)

    user.activate()

    assert user.state == UserState.ACTIVE
    assert user.version.version == 2


def test_freeze_changes_state(user_factory: Callable[..., User]) -> None:
    user = user_factory(state=UserState.ACTIVE)

    user.freeze()

    assert user.state == UserState.FROZEN
    assert user.version.version == 2


def test_delete_changes_state(user_factory: Callable[..., User]) -> None:
    user = user_factory(state=UserState.ACTIVE)

    user.delete()

    assert user.state == UserState.DELETED
    assert user.version.version == 2
