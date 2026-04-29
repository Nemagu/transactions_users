from abc import ABC, abstractmethod

from domain.user import Email


class EmailSender(ABC):
    @abstractmethod
    async def send(self, recipients: list[Email], body: str) -> None: ...


class EmailBodyBuilder(ABC):
    @abstractmethod
    async def confirm_email(self, code: int) -> str: ...

    @abstractmethod
    async def auth_code(self, code: int) -> str: ...

    @abstractmethod
    async def confirm_new_email(self, code: int) -> str: ...
