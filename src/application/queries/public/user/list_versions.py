from dataclasses import dataclass
from typing import Any
from uuid import UUID

from application.dto.paginators import LimitOffsetPaginator
from application.dto.user import UserVersionSimpleDTO
from application.queries.base import BaseUseCase
from domain.user import UserID, UserState, UserStatus
from domain.value_objects import Version


@dataclass
class UserVersionsQuery:
    initiator_id: UUID
    user_id: UUID
    paginator: LimitOffsetPaginator
    statuses: list[str] | None
    states: list[str] | None
    from_version: int | None
    to_version: int | None


class UserVersionsUseCase(BaseUseCase):
    """Получение нескольких версий пользователя с фильтрацией."""

    async def execute(
        self, query: UserVersionsQuery
    ) -> tuple[list[UserVersionSimpleDTO], int]:
        action = "получение нескольких версий пользователя"
        initiator_id = UserID(query.initiator_id)
        filtering_data = self._cast_data_from_query(query)
        async with self._uow as uow:
            initiator = await self._initiator(uow, initiator_id, action)
            if query.initiator_id != query.user_id:
                initiator.staff()
            user_versions, count = await uow.user_repositories.version.filters(
                **filtering_data
            )
            return [UserVersionSimpleDTO.from_dto(dto) for dto in user_versions], count

    def _cast_data_from_query(self, query: UserVersionsQuery) -> dict[str, Any]:
        data: dict[str, Any] = {
            "paginator": query.paginator,
            "user_id": UserID(query.user_id),
        }
        if query.statuses is not None:
            data["statuses"] = [UserStatus.from_str(status) for status in query.statuses]
        if query.states is not None:
            data["states"] = [UserState.from_str(state) for state in query.states]
        if query.from_version is not None:
            data["from_version"] = Version(query.from_version)
        if query.to_version is not None:
            data["to_version"] = Version(query.to_version)
        return data
