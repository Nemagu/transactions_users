import pytest

from infrastructure.email.body_builder import SimpleEmailBodyBuilder


@pytest.mark.asyncio
async def test_builders_escape_html() -> None:
    builder = SimpleEmailBodyBuilder()

    body = await builder.confirm_new_email(123456)

    assert "123456" in body
    assert "<script>" not in body
    assert "Подтверждение смены email" in body
