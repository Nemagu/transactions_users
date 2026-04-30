import pytest

from domain.errors import ValueObjectInvalidDataError
from domain.user.value_objects import UserState, UserStatus


@pytest.mark.parametrize(
    ("value", "expected"),
    [("ADMIN", UserStatus.ADMIN), ("user", UserStatus.USER)],
    ids=["admin-upper", "user-lower"],
)
def test_user_status_from_str(value: str, expected: UserStatus) -> None:
    assert UserStatus.from_str(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ACTIVE", UserState.ACTIVE),
        ("frozen", UserState.FROZEN),
        ("deleted", UserState.DELETED),
    ],
    ids=["active", "frozen", "deleted"],
)
def test_user_state_from_str(value: str, expected: UserState) -> None:
    assert UserState.from_str(value) == expected


@pytest.mark.parametrize(
    ("enum_cls", "value"),
    [(UserStatus, "owner"), (UserState, "archived")],
    ids=["invalid-status", "invalid-state"],
)
def test_user_enums_reject_invalid_values(enum_cls: type, value: str) -> None:
    with pytest.raises(ValueObjectInvalidDataError):
        enum_cls.from_str(value)
