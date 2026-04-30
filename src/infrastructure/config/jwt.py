"""JWT-конфигурация инфраструктурного слоя."""

from os import path
from typing import Self

from pydantic import BaseModel, model_validator


class JWTSettings(BaseModel):
    """Настройки JWT с асимметричным RS256 ключом."""

    algorithm: str = "RS256"
    private_key_file: str = "/tmp/transactions/jwt_private_key.pem"
    public_key_file: str | None = None

    issuer: str = "users"
    audience: str = "users_api"
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 2592000
    leeway_seconds: int = 0

    @model_validator(mode="after")
    def _validate_key_files(self) -> Self:
        """Проверяет наличие файлов ключей JWT."""
        if not path.isfile(self.private_key_file):
            raise ValueError(f"JWT private key file not found: {self.private_key_file}")
        if self.public_key_file is not None and not path.isfile(self.public_key_file):
            raise ValueError(f"JWT public key file not found: {self.public_key_file}")
        return self

    @property
    def private_key(self) -> str:
        """Возвращает содержимое приватного ключа."""
        with open(self.private_key_file, "r", encoding="utf-8") as file:
            return file.read()

    @property
    def public_key(self) -> str:
        """Возвращает содержимое публичного ключа."""
        key_file = self.public_key_file or self.private_key_file
        with open(key_file, "r", encoding="utf-8") as file:
            return file.read()
