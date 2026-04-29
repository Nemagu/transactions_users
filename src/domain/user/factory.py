from uuid import UUID

from domain.user.entity import User
from domain.user.value_objects import Email, UserID, UserState, UserStatus
from domain.value_objects import Version


class UserFactory:
    @staticmethod
    def new(user_id: UserID, email: Email) -> User:
        return User(user_id, email, UserStatus.USER, UserState.ACTIVE, Version(1))

    @staticmethod
    def restore(
        user_id: UUID, email: str, status: str, state: str, version: int
    ) -> User:
        return User(
            UserID(user_id),
            Email(email),
            UserStatus.from_str(status),
            UserState.from_str(state),
            Version(version),
        )
