from abc import ABC, abstractmethod
from typing import Sequence

from application.ports.repositories import UserVersionDTO

PublishEventDTO = UserVersionDTO


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: PublishEventDTO) -> None: ...

    @abstractmethod
    async def batch_publish(self, events: Sequence[PublishEventDTO]) -> None: ...
