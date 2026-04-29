from abc import ABC, abstractmethod


class PasswordManager(ABC):
    @abstractmethod
    async def validate(self, password: str) -> str | None: ...

    @abstractmethod
    async def hash(self, password: str) -> str: ...

    @abstractmethod
    async def verify(self, password: str, hashed: str) -> bool: ...

    @abstractmethod
    async def fake_verify(self) -> None: ...
