from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.user import Email


@dataclass(frozen=True)
class EmailMessage:
    """Готовое к отправке письмо: получатель, тема, html- и текстовое тело."""

    recipient: Email
    subject: str
    html_body: str
    text_body: str


class EmailSender(ABC):
    """Порт отправки сформированного письма во внешний email-сервис."""

    @abstractmethod
    async def send(self, message: EmailMessage) -> None: ...


class EmailMessageBuilder(ABC):
    """Порт сборки письма по шаблонам сценариев пользователя.

    Каждый метод возвращает готовое сообщение под конкретный сценарий:
    подтверждение регистрации, аутентификация по коду, смена email.
    """

    @abstractmethod
    async def confirm_email(self, recipient: Email, code: int) -> EmailMessage: ...

    @abstractmethod
    async def auth_code(self, recipient: Email, code: int) -> EmailMessage: ...

    @abstractmethod
    async def confirm_new_email(
        self, recipient: Email, code: int
    ) -> EmailMessage: ...
