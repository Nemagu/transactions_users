from dataclasses import dataclass
from datetime import timedelta

from application.command.base import BaseUseCase
from application.ports.email import EmailBodyBuilder, EmailSender
from application.ports.key_value_store import KeyValueStore
from application.ports.randomizer import Randomizer
from application.ports.unit_of_work import UnitOfWork
from domain.user import Email


@dataclass
class AuthCodeSendingCommand:
    email: str


class AuthCodeSendingUseCase(BaseUseCase):
    def __init__(
        self,
        uow: UnitOfWork,
        key_value_store: KeyValueStore,
        randomizer: Randomizer,
        email_sender: EmailSender,
        email_builder: EmailBodyBuilder,
    ) -> None:
        super().__init__(uow)
        self._kv_store = key_value_store
        self._randomizer = randomizer
        self._email_sender = email_sender
        self._email_builder = email_builder

    async def execute(self, command: AuthCodeSendingCommand) -> None:
        email = Email(command.email)
        async with self._uow as uow:
            user = await uow.user_repositories.read.by_email(email)
        if user is None:
            return
        code = await self._randomizer.number(8)
        await self._kv_store.set(
            f"users:code_auth:{email.email}", code, timedelta(minutes=5)
        )
        body = await self._email_builder.auth_code(code)
        await self._email_sender.send([email], body)
