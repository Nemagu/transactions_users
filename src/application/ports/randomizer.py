from abc import ABC, abstractmethod


class Randomizer(ABC):
    @abstractmethod
    async def number(self, len: int) -> int: ...
