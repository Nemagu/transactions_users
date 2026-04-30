import pytest

from infrastructure.config.db import PostgresSettings


def test_postgres_settings_rejects_missing_password_file(tmp_path) -> None:
    with pytest.raises(ValueError):
        PostgresSettings(password_file=str(tmp_path / "missing.txt"))


def test_postgres_settings_builds_urls(tmp_path) -> None:
    password_file = tmp_path / "db_password"
    password_file.write_text("secret\n", encoding="utf-8")

    settings = PostgresSettings(password_file=str(password_file))

    assert settings.password == "secret"
    assert settings.url == "postgresql://users:secret@localhost:5432/users"
    assert settings.url_with_psycopg == "postgresql+psycopg://users:secret@localhost:5432/users"
