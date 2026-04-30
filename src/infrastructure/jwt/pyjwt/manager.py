"""PyJWT-адаптер для работы с access/refresh токенами RS256."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt import InvalidTokenError
from pydantic import ValidationError

from application.errors import AppInternalError
from infrastructure.config.jwt import JWTSettings
from infrastructure.jwt.pyjwt.payload import JWTTokenPayload, TokenType


class PyJWTManager:
    """Менеджер JWT-токенов с предзагруженными ключами."""

    def __init__(self, settings: JWTSettings) -> None:
        self._algorithm = settings.algorithm
        self._issuer = settings.issuer
        self._audience = settings.audience
        self._access_ttl_seconds = settings.access_token_ttl_seconds
        self._refresh_ttl_seconds = settings.refresh_token_ttl_seconds
        self._leeway_seconds = settings.leeway_seconds
        self._private_key = settings.private_key
        self._public_key = settings.public_key

    def issue_access_token(self, user_id: UUID) -> str:
        """Создает access JWT токен."""
        return self._issue_token(
            user_id=user_id,
            token_type=TokenType.ACCESS,
            ttl=self._access_ttl_seconds,
        )

    def issue_refresh_token(self, user_id: UUID) -> str:
        """Создает refresh JWT токен."""
        return self._issue_token(
            user_id=user_id,
            token_type=TokenType.REFRESH,
            ttl=self._refresh_ttl_seconds,
        )

    def verify_access_token(self, token: str) -> bool:
        """Проверяет access токен и возвращает булево значение."""
        return self._verify(token=token, token_type=TokenType.ACCESS)

    def verify_refresh_token(self, token: str) -> bool:
        """Проверяет refresh токен и возвращает булево значение."""
        return self._verify(token=token, token_type=TokenType.REFRESH)

    def access_user_id(self, token: str) -> UUID | None:
        """Возвращает user_id из access токена или `None`."""
        return self._user_id(token=token, token_type=TokenType.ACCESS)

    def refresh_user_id(self, token: str) -> UUID | None:
        """Возвращает user_id из refresh токена или `None`."""
        return self._user_id(token=token, token_type=TokenType.REFRESH)

    def _issue_token(self, user_id: UUID, token_type: TokenType, ttl: int) -> str:
        now = datetime.now(tz=UTC)
        payload = JWTTokenPayload(
            user_id=user_id,
            token_type=token_type,
            iss=self._issuer,
            aud=self._audience,
            iat=int(now.timestamp()),
            nbf=int(now.timestamp()),
            exp=int((now + timedelta(seconds=ttl)).timestamp()),
        )
        try:
            return jwt.encode(
                payload=payload.model_dump(mode="json"),
                key=self._private_key,
                algorithm=self._algorithm,
            )
        except Exception as err:
            raise AppInternalError(
                msg="внутренняя ошибка генерации jwt токена",
                action="генерация jwt токена",
                wrap_error=err,
            ) from err

    def _verify(self, token: str, token_type: TokenType) -> bool:
        if not token:
            return False
        try:
            payload = JWTTokenPayload.model_validate(self._decode(token))
            return payload.token_type == token_type
        except (InvalidTokenError, ValidationError, ValueError):
            return False
        except Exception as err:
            raise AppInternalError(
                msg="внутренняя ошибка проверки jwt токена",
                action="проверка jwt токена",
                wrap_error=err,
            ) from err

    def _user_id(self, token: str, token_type: TokenType) -> UUID | None:
        if not token:
            return None
        try:
            payload = JWTTokenPayload.model_validate(self._decode(token))
            if payload.token_type != token_type:
                return None
            return payload.user_id
        except (InvalidTokenError, ValidationError, ValueError):
            return None
        except Exception as err:
            raise AppInternalError(
                msg="внутренняя ошибка извлечения user_id из jwt токена",
                action="извлечение user_id из jwt токена",
                wrap_error=err,
            ) from err

    def _decode(self, token: str) -> dict:
        return jwt.decode(
            jwt=token,
            key=self._public_key,
            algorithms=[self._algorithm],
            audience=self._audience,
            issuer=self._issuer,
            leeway=self._leeway_seconds,
            options={
                "require": ["exp", "iat", "nbf", "iss", "aud", "token_type", "user_id"],
            },
        )
