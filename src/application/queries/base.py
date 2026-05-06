from abc import ABC

from application.errors import AppInvalidDataError
from application.ports.unit_of_work import UnitOfWork
from domain.user import User, UserID


class BaseUseCase(ABC):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def _initiator(self, uow: UnitOfWork, initiator_id: UserID, action: str) -> User:
        initiator = await uow.user_repositories.read.by_id(initiator_id)
        if initiator is None:
            raise AppInvalidDataError(
                msg="инициатор не существует",
                action=action,
                data={"user": {"user_id": initiator_id.user_id}},
            )
        return initiator
