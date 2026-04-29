from abc import ABC, abstractmethod
from datetime import timedelta

Value = str | int


class KeyValueStore(ABC):
    @abstractmethod
    async def set(self, key: str, value: Value, duration: timedelta) -> None: ...

    @abstractmethod
    async def get_int(self, key: str) -> int | None: ...
