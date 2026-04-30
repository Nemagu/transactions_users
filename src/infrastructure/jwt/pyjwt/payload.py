"""Модели payload JWT-токена."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class TokenType(StrEnum):
    """Поддерживаемые типы JWT-токенов."""

    ACCESS = "access"
    REFRESH = "refresh"


class JWTTokenPayload(BaseModel):
    """Полный payload JWT-токена."""

    user_id: UUID
    token_type: TokenType
    iss: str
    aud: str
    iat: int
    nbf: int
    exp: int
