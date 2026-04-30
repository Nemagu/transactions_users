from uuid import uuid7

import pytest

from infrastructure.password_manager import Argon2PasswordManager


@pytest.mark.asyncio
async def test_health_check(api_client) -> None:
    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_password_auth_returns_user(pg_connection, api_client) -> None:
    user_id = uuid7()
    email = "auth@example.com"
    password = "Valid#123"
    pwd_manager = Argon2PasswordManager()
    try:
        hashed = await pwd_manager.hash(password)
    finally:
        pwd_manager.close()

    async with pg_connection.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO users (user_id, email, status, state, version)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, email, "user", "active", 1),
        )
        await cur.execute(
            """
            INSERT INTO users_passwords (password_hash, user_id)
            VALUES (%s, %s)
            """,
            (hashed, user_id),
        )
    await pg_connection.commit()

    response = await api_client.post(
        "/public/v1/users/auth/password",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(user_id)
    assert body["email"] == email
    assert body["status"] == "user"
    assert body["state"] == "active"


@pytest.mark.asyncio
async def test_password_auth_rejects_invalid_credentials(api_client) -> None:
    response = await api_client.post(
        "/public/v1/users/auth/password",
        json={"email": "missing@example.com", "password": "Wrong#123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "неверный email или пароль"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "authorization",
    [None, "Bearer", "Token abc", "Bearer invalid.token"],
    ids=["missing", "bearer-empty", "wrong-scheme", "invalid-jwt"],
)
async def test_protected_endpoint_requires_valid_bearer_token(
    api_client,
    authorization: str | None,
) -> None:
    headers = {}
    if authorization is not None:
        headers["Authorization"] = authorization

    response = await api_client.put(
        f"/public/v1/users/{uuid7()}/freeze",
        headers=headers,
    )

    assert response.status_code == 401
