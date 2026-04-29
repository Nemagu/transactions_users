from abc import ABC, abstractmethod

from domain.user import User, UserID


class UserPasswordRepository(ABC):
    @abstractmethod
    async def by_user_id(self, user_id: UserID) -> str | None: ...

    @abstractmethod
    async def save(self, user: User, hashed_password: str) -> None: ...
