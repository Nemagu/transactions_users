from dataclasses import dataclass
from uuid import UUID

from application.dto.user import UserVersionSimpleDTO
from application.errors import AppInvalidDataError
from application.queries.base import BaseUseCase
from domain.user import UserID
from domain.value_objects import Version


@dataclass
class UserVersionQuery:
    initiator_id: UUID
    user_id: UUID
    version: int


class UserVersionUseCase(BaseUseCase):
    """Получение одной из версий пользователя."""

    async def execute(self, query: UserVersionQuery) -> UserVersionSimpleDTO:
        action = "получение одной из версий пользователя"
        initiator_id = UserID(query.initiator_id)
        user_id = UserID(query.user_id)
        version = Version(query.version)
        async with self._uow as uow:
            initiator = await self._initiator(uow, initiator_id, action)
            if query.initiator_id != query.user_id:
                initiator.staff()
            user_version = await uow.user_repositories.version.by_id_version(user_id, version)
            if user_version is None:
                raise AppInvalidDataError(
                    msg="пользователь такой версии не существует",
                    action=action,
                    data={"user": {"user_id": query.user_id, "version": query.version}},
                )
            return UserVersionSimpleDTO.from_dto(user_version)
