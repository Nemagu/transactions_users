from dataclasses import dataclass
from uuid import UUID

from application.command.base import BaseUseCase
from application.dto.user import UserSimpleDTO
from application.errors import AppInvalidDataError
from application.ports.key_value_store import KeyValueStore
from application.ports.repositories import UserEvent
from application.ports.unit_of_work import UnitOfWork
from domain.user import Email, UserID


@dataclass
class UserEmailChangingCommand:
    initiator_id: UUID
    new_email: str
    new_email_code: int
    old_email_code: int


class UserEmailChangingUseCase(BaseUseCase):
    def __init__(
        self,
        uow: UnitOfWork,
        key_value_store: KeyValueStore,
    ) -> None:
        super().__init__(uow)
        self._kv_store = key_value_store

    async def execute(self, command: UserEmailChangingCommand) -> UserSimpleDTO:
        action = "изменение email пользователя"
        new_email = Email(command.new_email)
        initiator_id = UserID(command.initiator_id)
        async with self._uow as uow:
            initiator = await self._initiator(uow, initiator_id, action)
        new_email_code = await self._kv_store.get_int(
            f"users:confirm_new_email:{new_email.email}"
        )
        old_email_code = await self._kv_store.get_int(
            f"users:confirm_new_email:{initiator.email.email}"
        )
        if (
            new_email_code is None
            or old_email_code is None
            or new_email_code != command.new_email_code
            or old_email_code != command.old_email_code
        ):
            raise AppInvalidDataError(msg="не верный код подтверждения", action=action)
        initiator.new_email(new_email)
        async with self._uow as uow:
            await uow.user_repositories.read.save(initiator)
            await uow.user_repositories.version.save(
                initiator, UserEvent.UPDATED, initiator_id
            )
        return UserSimpleDTO.from_domain(initiator)
