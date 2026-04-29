from abc import ABC, abstractmethod

from domain.user.entity import User
from domain.user.value_objects import Email


class UserReadRepository(ABC):
    @abstractmethod
    async def by_email(self, email: Email) -> User | None: ...
