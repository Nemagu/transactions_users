from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from domain.errors import ValueObjectInvalidDataError


@dataclass(frozen=True)
class UserID:
    user_id: UUID


@dataclass(frozen=True)
class Email:
    email: str


class UserStatus(StrEnum):
    ADMIN = "admin"
    USER = "user"

    @classmethod
    def from_str(cls, value: str) -> Self:
        lower_value = value.lower()
        if lower_value in cls._value2member_map_:
            return cls(lower_value)
        raise ValueObjectInvalidDataError(
            msg=(
                f"не удалось найти статус пользователя по предоставленной строке - "
                f'"{value}"'
            ),
            struct_name="статус пользователя",
            data={"status": value},
        )


class UserState(StrEnum):
    ACTIVE = "active"
    FROZEN = "frozen"
    DELETED = "deleted"

    def is_active(self) -> bool:
        return self == self.__class__.ACTIVE

    def is_frozen(self) -> bool:
        return self == self.__class__.FROZEN

    def is_deleted(self) -> bool:
        return self == self.__class__.DELETED

    @classmethod
    def from_str(cls, value: str) -> Self:
        lower_value = value.lower()
        if lower_value in cls._value2member_map_:
            return cls(lower_value)
        raise ValueObjectInvalidDataError(
            msg=(
                f"не удалось найти состояние пользователя по предоставленной строке - "
                f'"{value}"'
            ),
            struct_name="состояние пользователя",
            data={"state": value},
        )
