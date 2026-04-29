from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from application.errors import AppInternalError
from application.ports.password_manager import PasswordManager

__all__ = ["Argon2PasswordManager"]


class Argon2PasswordManager(PasswordManager):
    def __init__(self) -> None:
        self._hasher = PasswordHasher()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._fake_hashed_password = self._hasher.hash("fake-password-value")

    async def hash(self, password: str) -> str:
        """Создает хеш пароля с использованием argon2."""
        try:
            return await self._run_in_executor(self._hasher.hash, password)
        except Exception as err:
            raise AppInternalError(
                msg="не удалось захешировать пароль",
                action="хеширование пароля",
                wrap_error=err,
            ) from err

    async def verify(self, password: str, hashed: str) -> bool:
        """Проверяет пароль по ранее сохраненному хешу."""
        return await self._verify(password=password, hashed_password=hashed)

    async def fake_verify(self) -> None:
        """Выполняет фиктивную проверку для выравнивания времени ответа."""
        await self._verify(
            password="another-password-value",
            hashed_password=self._fake_hashed_password,
        )

    def close(self) -> None:
        """Останавливает executor с ожиданием завершения активных задач."""
        self._executor.shutdown(wait=True, cancel_futures=False)

    async def _verify(self, password: str, hashed_password: str) -> bool:
        try:
            return await self._run_in_executor(
                self._hasher.verify, hashed_password, password
            )
        except VerifyMismatchError:
            return False
        except (InvalidHashError, VerificationError) as err:
            raise AppInternalError(
                msg="ошибка верификации пароля",
                action="проверка пароля по хешу",
                wrap_error=err,
            ) from err

    async def _run_in_executor(self, func, *args):
        loop = get_running_loop()
        return await loop.run_in_executor(self._executor, func, *args)
