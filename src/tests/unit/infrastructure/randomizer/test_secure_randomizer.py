import pytest

from application.errors import AppInvalidDataError
from infrastructure.randomizer import SecureRandomizer


@pytest.mark.asyncio
async def test_number_returns_value_with_expected_length():
    value = await SecureRandomizer().number(6)

    assert 100000 <= value <= 999999


@pytest.mark.asyncio
async def test_number_raises_on_invalid_length():
    with pytest.raises(AppInvalidDataError) as exc_info:
        await SecureRandomizer().number(0)

    assert exc_info.value.data == {"len": 0}
