from abc import ABC

from application.errors import AppInvalidDataError
from application.ports.event_publisher import EventPublisher
from application.ports.unit_of_work import UnitOfWork
from domain.user import User, UserID


class BaseUseCase(ABC):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow: UnitOfWork = uow

    async def _initiator(
        self, uow: UnitOfWork, initiator_id: UserID, action: str
    ) -> User:
        initiator = await uow.user_repositories.read.by_id(initiator_id)
        if initiator is None:
            raise AppInvalidDataError(
                msg="инициатор не существует",
                action=action,
                data={"user": {"user_id": initiator_id.user_id}},
            )
        return initiator


class PublicationUseCase(BaseUseCase):
    def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
        super().__init__(uow)
        self._event_publisher = event_publisher
