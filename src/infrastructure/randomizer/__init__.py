from secrets import randbelow

from application.errors import AppInvalidDataError
from application.ports.randomizer import Randomizer

__all__ = ["SecureRandomizer"]


class SecureRandomizer(Randomizer):
    async def number(self, len: int) -> int:
        """Возвращает случайное число заданной длины."""
        if len < 1:
            raise AppInvalidDataError(
                msg="длина случайного числа должна быть больше нуля",
                action="генерация случайного числа",
                data={"len": len},
            )

        min_value = 10 ** (len - 1)
        max_value = (10**len) - 1
        return min_value + randbelow(max_value - min_value + 1)
