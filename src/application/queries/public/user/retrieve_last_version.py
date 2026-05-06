from dataclasses import dataclass
from uuid import UUID

from application.dto.user import UserSimpleDTO
from application.errors import AppInvalidDataError
from application.queries.base import BaseUseCase
from domain.user import UserID


@dataclass
class UserLastVersionQuery:
    initiator_id: UUID
    user_id: UUID


class UserLastVersionUseCase(BaseUseCase):
    """Получение последней версии пользователя."""

    async def execute(self, query: UserLastVersionQuery) -> UserSimpleDTO:
        action = "получение последней версии пользователя"
        initiator_id = UserID(query.initiator_id)
        user_id = UserID(query.user_id)
        async with self._uow as uow:
            initiator = await self._initiator(uow, initiator_id, action)
            if query.initiator_id != query.user_id:
                initiator.staff()
                user = await uow.user_repositories.read.by_id(user_id)
                if user is None:
                    raise AppInvalidDataError(
                        msg="пользователь не существует",
                        action=action,
                        data={"user": {"user_id": query.user_id}},
                    )
                return UserSimpleDTO.from_domain(user)
            return UserSimpleDTO.from_domain(initiator)
