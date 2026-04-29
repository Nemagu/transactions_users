from dataclasses import dataclass

from application.command.base import BaseUseCase
from application.dto.user import UserSimpleDTO
from application.errors import AppInvalidDataError
from application.ports.key_value_store import KeyValueStore
from application.ports.unit_of_work import UnitOfWork
from domain.user import Email


@dataclass
class CodeAuthCommand:
    email: str
    code: int


class CodeAuthUseCase(BaseUseCase):
    def __init__(self, uow: UnitOfWork, key_value_store: KeyValueStore) -> None:
        super().__init__(uow)
        self._kv_store = key_value_store

    async def execute(self, command: CodeAuthCommand) -> UserSimpleDTO:
        action = "аутентификация через одноразовый код"
        email = Email(command.email)
        async with self._uow as uow:
            user = await uow.user_repositories.read.by_email(email)
        code = await self._kv_store.get_int(f"users:code_auth:{email.email}")
        if user is None or code is None or code != command.code:
            raise AppInvalidDataError(msg="неверный email или код", action=action)
        return UserSimpleDTO.from_domain(user)
