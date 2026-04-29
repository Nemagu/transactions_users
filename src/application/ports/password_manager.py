from abc import ABC, abstractmethod


class PasswordManager(ABC):
    async def validate(self, password: str) -> str | None:
        """Проверяет пароль на соответствие базовым требованиям."""
        if len(password) < 8:
            return "длина пароля должна быть не менее 8 символов"
        if len(password) > 128:
            return "длина пароля должна быть не более 128 символов"
        if not any(char.isupper() for char in password):
            return "пароль должен содержать хотя бы одну заглавную букву"
        if not any(char.islower() for char in password):
            return "пароль должен содержать хотя бы одну строчную букву"
        if not any(char.isdigit() for char in password):
            return "пароль должен содержать хотя бы одну цифру"
        if not any(not char.isalnum() for char in password):
            return "пароль должен содержать хотя бы один спецсимвол"
        return None

    @abstractmethod
    async def hash(self, password: str) -> str: ...

    @abstractmethod
    async def verify(self, password: str, hashed: str) -> bool: ...

    @abstractmethod
    async def fake_verify(self) -> None: ...
