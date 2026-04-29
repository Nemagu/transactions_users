from dataclasses import dataclass
from uuid import UUID

from application.command.base import BaseUseCase
from application.dto.user import UserSimpleDTO
from application.errors import AppNotFoundError
from application.ports.repositories import UserEvent
from domain.user import UserID


@dataclass
class UserAppointingAdminCommand:
    initiator_id: UUID
    user_id: UUID


class UserAppointingAdminUseCase(BaseUseCase):
    async def execute(self, command: UserAppointingAdminCommand) -> UserSimpleDTO:
        action = "назначение пользователя администратором"
        initiator_id = UserID(command.initiator_id)
        user_id = UserID(command.user_id)
        async with self._uow as uow:
            initiator = await self._initiator(uow, initiator_id, action)
            initiator.staff()
            user = await uow.user_repositories.read.by_id(user_id)
            if user is None:
                raise AppNotFoundError(
                    msg="пользователя не существует",
                    action=action,
                    data={"user": {"user_id": user_id.user_id}},
                )
            user.appoint_admin()
            await uow.user_repositories.read.save(user)
            await uow.user_repositories.version.save(
                user, UserEvent.UPDATED, initiator_id
            )
            return UserSimpleDTO.from_domain(user)
