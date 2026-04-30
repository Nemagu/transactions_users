from fastapi import Request

from infrastructure.password_manager import Argon2PasswordManager


async def password_manager(request: Request) -> Argon2PasswordManager:
    return request.app.state.password_manager
