from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Self

from application.dto.paginators import LimitOffsetPaginator
from application.errors import AppInvalidDataError
from domain.user import User, UserID, UserState, UserStatus
from domain.user import UserReadRepository as DomainUserReadRepository
from domain.value_objects import Version


class UserReadRepository(DomainUserReadRepository):
    @abstractmethod
    async def next_id(self) -> UserID: ...

    @abstractmethod
    async def by_id(self, user_id: UserID) -> User | None: ...

    @abstractmethod
    async def filters(
        self,
        paginator: LimitOffsetPaginator,
        user_ids: list[UserID] | None = None,
        statuses: list[UserStatus] | None = None,
        states: list[UserState] | None = None,
    ) -> tuple[list[User], int]: ...

    @abstractmethod
    async def save(self, user: User) -> None: ...


class UserEvent(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    FROZEN = "frozen"
    DELETED = "deleted"
    RESTORED = "restored"

    @classmethod
    def from_str(cls, value: str) -> Self:
        lower_value = value.lower()
        if lower_value in cls._value2member_map_:
            return cls(lower_value)
        raise AppInvalidDataError(
            msg=(
                f"не удалось найти событие пользователя по предоставленной строке - "
                f'"{value}"'
            ),
            action="событие пользователя",
            data={"event": value},
        )


@dataclass
class UserVersionDTO:
    user: User
    event: UserEvent
    editor_id: UserID | None
    created_at: datetime


class UserVersionRepository(ABC):
    @abstractmethod
    async def by_id_version(
        self, user_id: UserID, version: Version
    ) -> UserVersionDTO | None: ...

    @abstractmethod
    async def filters(
        self,
        paginator: LimitOffsetPaginator,
        user_id: UserID,
        statuses: list[UserStatus] | None = None,
        states: list[UserState] | None = None,
        from_version: Version | None = None,
        to_version: Version | None = None,
    ) -> tuple[list[UserVersionDTO], int]: ...

    @abstractmethod
    async def save(
        self, user: User, event: UserEvent, editor_id: UserID | None
    ) -> None: ...

    @abstractmethod
    async def batch_save(
        self, users_events_editor_ids: list[tuple[User, UserEvent, UserID | None]]
    ) -> None: ...


class UserOutboxRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def batch_save(self, users: list[User]) -> None: ...

    @abstractmethod
    async def not_published_versions(self) -> list[UserVersionDTO]: ...
