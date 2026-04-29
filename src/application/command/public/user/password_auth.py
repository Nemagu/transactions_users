from dataclasses import dataclass
from uuid import uuid7

from application.command.base import BaseUseCase
from application.dto.user import UserSimpleDTO
from application.errors import AppInvalidDataError
from application.ports.password_manager import PasswordManager
from application.ports.unit_of_work import UnitOfWork
from domain.user import Email, UserID


@dataclass
class PasswordAuthCommand:
    email: str
    password: str


class PasswordAuthUseCase(BaseUseCase):
    def __init__(self, uow: UnitOfWork, password_manager: PasswordManager) -> None:
        super().__init__(uow)
        self._pwd_manager = password_manager

    async def execute(self, command: PasswordAuthCommand) -> UserSimpleDTO:
        action = "аутентификация через email и пароль"
        email = Email(command.email)
        error = AppInvalidDataError(
            msg="неверный email или пароль",
            action=action,
        )
        async with self._uow as uow:
            user = await uow.user_repositories.read.by_email(email)
            user_id = user.user_id if user is not None else UserID(uuid7())
            hashed_pwd = await uow.user_password_repositories.read.by_user_id(user_id)
        if user is None or hashed_pwd is None:
            await self._pwd_manager.fake_verify()
            raise error
        if not await self._pwd_manager.verify(command.password, hashed_pwd):
            raise error
        return UserSimpleDTO.from_domain(user)
