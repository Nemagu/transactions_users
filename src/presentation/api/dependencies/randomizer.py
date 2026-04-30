from fastapi import Request

from infrastructure.randomizer import SecureRandomizer


async def randomizer(request: Request) -> SecureRandomizer:
    return request.app.state.randomizer
