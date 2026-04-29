from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from application.command.base import BaseUseCase
from application.errors import AppInvalidDataError
from application.ports.email import EmailBodyBuilder, EmailSender
from application.ports.key_value_store import KeyValueStore
from application.ports.randomizer import Randomizer
from application.ports.unit_of_work import UnitOfWork
from domain.user import Email, UserID


@dataclass
class NewEmailConfirmingCommand:
    initiator_id: UUID
    new_email: str


class NewEmailConfirmingUseCase(BaseUseCase):
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

    async def execute(self, command: NewEmailConfirmingCommand) -> None:
        action = "подтверждение новой почты"
        new_email = Email(command.new_email)
        initiator_id = UserID(command.initiator_id)
        async with self._uow as uow:
            initiator = await self._initiator(uow, initiator_id, action)
            exists_user = await uow.user_repositories.read.by_email(new_email)
            if exists_user is not None:
                raise AppInvalidDataError(
                    msg="такой email уже существует",
                    action=action,
                    data={"user": {"email": new_email.email}},
                )
            old_email = initiator.email
            initiator.new_email(new_email)
        old_email_code = await self._randomizer.number(8)
        new_email_code = await self._randomizer.number(8)
        await self._kv_store.set(
            f"users:confirm_new_email:{old_email.email}",
            old_email_code,
            timedelta(minutes=5),
        )
        await self._kv_store.set(
            f"users:confirm_new_email:{new_email.email}",
            new_email_code,
            timedelta(minutes=5),
        )
        old_email_body = await self._email_builder.confirm_new_email(old_email_code)
        new_email_body = await self._email_builder.confirm_new_email(new_email_code)
        await self._email_sender.send([old_email], old_email_body)
        await self._email_sender.send([new_email], new_email_body)
