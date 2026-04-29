from dataclasses import dataclass

from application.ports.repositories.password import UserPasswordRepository
from application.ports.repositories.user import (
    UserEvent,
    UserOutboxRepository,
    UserReadRepository,
    UserVersionDTO,
    UserVersionRepository,
)

__all__ = [
    "UserEvent",
    "UserOutboxRepository",
    "UserPasswordRepositories",
    "UserPasswordRepository",
    "UserReadRepository",
    "UserRepositories",
    "UserVersionDTO",
    "UserVersionRepository",
]


@dataclass
class UserRepositories:
    read: UserReadRepository
    version: UserVersionRepository
    outbox: UserOutboxRepository


@dataclass
class UserPasswordRepositories:
    read: UserPasswordRepository
