from datetime import datetime, timezone
from uuid import uuid4

import pytest

from application.errors import AppInternalError
from infrastructure.config.jwt import JWTSettings
from infrastructure.jwt.pyjwt import PyJWTManager


def _settings(tmp_path):
    private_key_file = tmp_path / "private.pem"
    public_key_file = tmp_path / "public.pem"
    private_key_file.write_text("PRIVATE", encoding="utf-8")
    public_key_file.write_text("PUBLIC", encoding="utf-8")
    return JWTSettings(
        private_key_file=str(private_key_file),
        public_key_file=str(public_key_file),
    )


def _payload(user_id: str, token_type: str) -> dict:
    now = int(datetime.now(tz=timezone.utc).timestamp())
    return {
        "user_id": user_id,
        "token_type": token_type,
        "iss": "users",
        "aud": "users_api",
        "iat": now,
        "nbf": now,
        "exp": now + 60,
    }


def test_verify_access_and_refresh(monkeypatch, tmp_path) -> None:
    manager = PyJWTManager(_settings(tmp_path))

    monkeypatch.setattr(
        "infrastructure.jwt.pyjwt.manager.jwt.decode",
        lambda **kwargs: _payload(str(uuid4()), "access"),
    )

    assert manager.verify_access_token("token") is True
    assert manager.verify_refresh_token("token") is False


def test_user_id_access_and_refresh(monkeypatch, tmp_path) -> None:
    user_id = uuid4()
    manager = PyJWTManager(_settings(tmp_path))

    monkeypatch.setattr(
        "infrastructure.jwt.pyjwt.manager.jwt.decode",
        lambda **kwargs: _payload(str(user_id), "refresh"),
    )

    assert manager.access_user_id("token") is None
    assert manager.refresh_user_id("token") == user_id


def test_invalid_token_returns_false_or_none(monkeypatch, tmp_path) -> None:
    manager = PyJWTManager(_settings(tmp_path))

    class InvalidTokenError(Exception):
        pass

    monkeypatch.setattr(
        "infrastructure.jwt.pyjwt.manager.InvalidTokenError",
        InvalidTokenError,
    )

    def broken_decode(**kwargs):
        raise InvalidTokenError("bad")

    monkeypatch.setattr("infrastructure.jwt.pyjwt.manager.jwt.decode", broken_decode)

    assert manager.verify_access_token("bad") is False
    assert manager.access_user_id("bad") is None


def test_internal_error_is_wrapped(monkeypatch, tmp_path) -> None:
    manager = PyJWTManager(_settings(tmp_path))

    def broken_decode(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("infrastructure.jwt.pyjwt.manager.jwt.decode", broken_decode)

    with pytest.raises(AppInternalError):
        manager.verify_access_token("token")
    with pytest.raises(AppInternalError):
        manager.access_user_id("token")


def test_issue_tokens(monkeypatch, tmp_path) -> None:
    manager = PyJWTManager(_settings(tmp_path))
    captured = {}

    def fake_encode(*, payload, key, algorithm):
        captured["payload"] = payload
        captured["key"] = key
        captured["algorithm"] = algorithm
        return "token"

    monkeypatch.setattr("infrastructure.jwt.pyjwt.manager.jwt.encode", fake_encode)

    token = manager.issue_access_token(uuid4())

    assert token == "token"
    assert captured["algorithm"] == "RS256"
    assert captured["key"] == "PRIVATE"
    assert captured["payload"]["token_type"] == "access"
