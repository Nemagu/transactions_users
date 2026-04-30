import pytest

from infrastructure.config.jwt import JWTSettings


def test_jwt_settings_rejects_missing_private_key_file(tmp_path) -> None:
    with pytest.raises(ValueError):
        JWTSettings(private_key_file=str(tmp_path / "missing.pem"))


def test_jwt_settings_returns_key_contents(tmp_path) -> None:
    private_key_file = tmp_path / "private.pem"
    public_key_file = tmp_path / "public.pem"
    private_key_file.write_text("PRIVATE_KEY", encoding="utf-8")
    public_key_file.write_text("PUBLIC_KEY", encoding="utf-8")

    settings = JWTSettings(
        private_key_file=str(private_key_file),
        public_key_file=str(public_key_file),
    )

    assert settings.private_key == "PRIVATE_KEY"
    assert settings.public_key == "PUBLIC_KEY"
