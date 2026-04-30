from uuid import UUID

from fastapi import HTTPException, Request, status


async def user_id_extractor(request: Request) -> UUID:
    """Извлекает user_id из access JWT токена в заголовке Authorization."""
    raw_auth = request.headers.get("authorization")
    if raw_auth is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "токен не передан")

    scheme, _, token = raw_auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "некорректный формат токена")

    user_id = request.app.state.jwt_manager.access_user_id(token)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "токен невалиден")
    return user_id
