import pytest

from application.errors import AppInternalError
from infrastructure.password_manager import Argon2PasswordManager


@pytest.mark.asyncio
async def test_hash_and_verify_roundtrip() -> None:
    manager = Argon2PasswordManager()
    try:
        hashed = await manager.hash("pass-123")

        assert await manager.verify("pass-123", hashed) is True
        assert await manager.verify("wrong", hashed) is False
    finally:
        manager.close()


@pytest.mark.asyncio
async def test_verify_raises_for_invalid_hash() -> None:
    manager = Argon2PasswordManager()
    try:
        with pytest.raises(AppInternalError):
            await manager.verify("pass-123", "invalid-hash")
    finally:
        manager.close()
