from dataclasses import dataclass
from typing import Any
from uuid import UUID

from application.dto.paginators import LimitOffsetPaginator
from application.dto.user import UserSimpleDTO
from application.queries.base import BaseUseCase
from domain.user import UserID, UserState, UserStatus


@dataclass
class UserLastVersionsQuery:
    initiator_id: UUID
    paginator: LimitOffsetPaginator
    user_ids: list[UUID] | None
    statuses: list[str] | None
    states: list[str] | None


class UserLastVersionsUseCase(BaseUseCase):
    """Получение последних версий пользователей с фильтрацией."""

    async def execute(
        self, query: UserLastVersionsQuery
    ) -> tuple[list[UserSimpleDTO], int]:
        action = "получение последних версий пользователей"
        initiator_id = UserID(query.initiator_id)
        filtering_data = self._cast_data_from_query(query)
        async with self._uow as uow:
            initiator = await self._initiator(uow, initiator_id, action)
            if (
                query.user_ids is not None
                and len(query.user_ids) == 1
                and query.initiator_id == query.user_ids[0]
            ):
                pass
            else:
                initiator.staff()
            users, count = await uow.user_repositories.read.filters(**filtering_data)
            return [UserSimpleDTO.from_domain(user) for user in users], count

    def _cast_data_from_query(self, query: UserLastVersionsQuery) -> dict[str, Any]:
        data: dict[str, Any] = {"paginator": query.paginator}
        if query.user_ids is not None:
            data["user_ids"] = [UserID(user_id) for user_id in query.user_ids]
        if query.statuses is not None:
            data["statuses"] = [UserStatus.from_str(status) for status in query.statuses]
        if query.states is not None:
            data["states"] = [UserState.from_str(state) for state in query.states]
        return data
