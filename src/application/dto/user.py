from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID

from application.ports.repositories import UserVersionDTO
from domain.user import User


@dataclass
class UserSimpleDTO:
    user_id: UUID
    email: str
    status: str
    state: str
    version: int

    @classmethod
    def from_domain(cls, user: User) -> Self:
        return cls(
            user.user_id.user_id,
            user.email.email,
            user.status.value,
            user.state.value,
            user.version.version,
        )


@dataclass
class UserVersionSimpleDTO:
    user_id: UUID
    email: str
    status: str
    state: str
    version: int
    event: str
    editor_id: UUID | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: UserVersionDTO) -> Self:
        return cls(
            dto.user.user_id.user_id,
            dto.user.email.email,
            dto.user.status.value,
            dto.user.state.value,
            dto.user.version.version,
            dto.event.value,
            dto.editor_id.user_id if dto.editor_id is not None else None,
            dto.created_at,
        )
