from dataclasses import dataclass

from application.command.base import BaseUseCase
from application.dto.user import UserSimpleDTO
from application.errors import AppInvalidDataError
from application.ports.key_value_store import KeyValueStore
from application.ports.password_manager import PasswordManager
from application.ports.repositories import UserEvent
from application.ports.unit_of_work import UnitOfWork
from domain.user import Email, UserFactory


@dataclass
class UserCreatingCommand:
    email: str
    code: int
    password: str


class UserCreatingUseCase(BaseUseCase):
    def __init__(
        self,
        uow: UnitOfWork,
        key_value_store: KeyValueStore,
        password_manager: PasswordManager,
    ) -> None:
        super().__init__(uow)
        self._kv_store = key_value_store
        self._pwd_manager = password_manager

    async def execute(self, command: UserCreatingCommand) -> UserSimpleDTO:
        action = "создание пользователя"
        email = Email(command.email)
        async with self._uow as uow:
            user = await uow.user_repositories.read.by_email(email)
            if user is not None:
                raise AppInvalidDataError(
                    msg="такой email уже существует",
                    action=action,
                    data={"user": {"email": email.email}},
                )
            user_id = await uow.user_repositories.read.next_id()
        code = await self._kv_store.get_int(f"users:confirm_email:{email.email}")
        if code is None or code != command.code:
            raise AppInvalidDataError(
                msg="не верный код подтверждения",
                action=action,
                data={"code": command.code},
            )
        pwd_error = await self._pwd_manager.validate(command.password)
        if pwd_error is not None:
            raise AppInvalidDataError(
                msg=f"не корректный пароль: {pwd_error}",
                action=action,
            )
        hashed_pwd = await self._pwd_manager.hash(command.password)
        user = UserFactory.new(user_id, email)
        async with self._uow as uow:
            await uow.user_repositories.read.save(user)
            await uow.user_repositories.version.save(user, UserEvent.CREATED, user_id)
            await uow.user_password_repositories.read.save(user, hashed_pwd)
        return UserSimpleDTO.from_domain(user)
