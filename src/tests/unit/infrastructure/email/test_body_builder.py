import pytest

from domain.user import Email
from infrastructure.email.body_builder import SimpleEmailMessageBuilder


@pytest.fixture
def builder() -> SimpleEmailMessageBuilder:
    return SimpleEmailMessageBuilder()


@pytest.fixture
def recipient() -> Email:
    return Email("user@example.com")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "expected_subject"),
    [
        ("confirm_email", "Подтверждение регистрации"),
        ("auth_code", "Код для входа"),
        ("confirm_new_email", "Подтверждение смены email"),
    ],
    ids=["confirm_email", "auth_code", "confirm_new_email"],
)
async def test_builder_returns_full_email_content(
    builder: SimpleEmailMessageBuilder,
    recipient: Email,
    method_name: str,
    expected_subject: str,
) -> None:
    code = 123456

    content = await getattr(builder, method_name)(recipient, code)

    assert content.recipient == recipient
    assert content.subject == expected_subject
    assert content.html_body.startswith("<!DOCTYPE html>")
    assert "<html" in content.html_body
    assert "<head>" in content.html_body
    assert "<body" in content.html_body
    assert f"<title>{expected_subject}</title>" in content.html_body
    assert str(code) in content.html_body
    assert expected_subject in content.text_body
    assert str(code) in content.text_body
    assert "<" not in content.text_body
