import pytest

from domain.errors import ValueObjectInvalidDataError
from domain.value_objects import AggregateName, ProjectionName, State, Version


@pytest.mark.parametrize(
    ("value", "expected"),
    [("active", State.ACTIVE), ("DELETED", State.DELETED)],
    ids=["active", "deleted-upper"],
)
def test_state_from_str_parses_values(value: str, expected: State) -> None:
    assert State.from_str(value) == expected


def test_state_from_str_raises_for_unknown_value() -> None:
    with pytest.raises(ValueObjectInvalidDataError):
        State.from_str("unknown")


@pytest.mark.parametrize(
    "version",
    [0, -1],
    ids=["zero", "negative"],
)
def test_version_rejects_non_positive_values(version: int) -> None:
    with pytest.raises(ValueObjectInvalidDataError):
        Version(version)


@pytest.mark.parametrize(
    ("cls", "value", "error"),
    [
        (AggregateName, "", ValueObjectInvalidDataError),
        (ProjectionName, "   ", ValueObjectInvalidDataError),
        (AggregateName, "x" * 51, ValueObjectInvalidDataError),
        (ProjectionName, "x" * 51, ValueObjectInvalidDataError),
    ],
    ids=["aggregate-empty", "projection-empty", "aggregate-too-long", "projection-too-long"],
)
def test_names_reject_invalid_values(cls: type, value: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        cls(value)


def test_aggregate_name_strips_spaces() -> None:
    assert AggregateName("  users  ").name == "users"
