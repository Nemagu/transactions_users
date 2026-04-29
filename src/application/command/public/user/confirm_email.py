from dataclasses import dataclass
from datetime import timedelta

from application.command.base import BaseUseCase
from application.errors import AppInvalidDataError
from application.ports.email import EmailBodyBuilder, EmailSender
from application.ports.key_value_store import KeyValueStore
from application.ports.randomizer import Randomizer
from application.ports.unit_of_work import UnitOfWork
from domain.user import Email


@dataclass
class UserConfirmingEmailCommand:
    email: str


class UserConfirmingEmailUseCase(BaseUseCase):
    def __init__(
        self,
        uow: UnitOfWork,
        key_value_store: KeyValueStore,
        email_sender: EmailSender,
        email_builder: EmailBodyBuilder,
        randomizer: Randomizer,
    ) -> None:
        super().__init__(uow)
        self._kv_store = key_value_store
        self._email_sender = email_sender
        self._email_builder = email_builder
        self._randomizer = randomizer

    async def execute(self, command: UserConfirmingEmailCommand) -> None:
        action = "подтверждение электронной почты для регистрации"
        email = Email(command.email)
        code = await self._randomizer.number(8)
        body = await self._email_builder.confirm_email(code)
        async with self._uow as uow:
            user = await uow.user_repositories.read.by_email(email)
            if user is not None:
                raise AppInvalidDataError(
                    msg="такой email уже существует",
                    action=action,
                    data={"user": {"email": email.email}},
                )
        await self._kv_store.set(
            f"users:confirm_email:{email.email}", code, timedelta(minutes=5)
        )
        await self._email_sender.send([email], body)
