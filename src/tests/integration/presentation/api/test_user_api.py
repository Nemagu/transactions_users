from collections.abc import Callable
from uuid import UUID, uuid7

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


async def _insert_user(pg_connection, user_id: UUID, email: str, status: str = "user") -> None:
    async with pg_connection.cursor() as cur:
        await cur.execute(
            "INSERT INTO users (user_id, email, status, state, version) VALUES (%s, %s, %s, %s, %s)",
            (user_id, email, status, "active", 1),
        )
    await pg_connection.commit()


async def _insert_version(pg_connection, user_id: UUID, email: str, version: int = 1, status: str = "user") -> None:
    async with pg_connection.cursor() as cur:
        await cur.execute(
            """INSERT INTO users_versions (user_id, email, status, state, version, event)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, email, status, "active", version, "created"),
        )
    await pg_connection.commit()


@pytest.mark.asyncio
async def test_get_user_self_access(pg_connection, api_client, jwt_access_token: Callable[[UUID], str]) -> None:
    user_id = uuid7()
    await _insert_user(pg_connection, user_id, "self@example.com")
    token = jwt_access_token(user_id)

    response = await api_client.get(
        f"/public/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(user_id)
    assert body["email"] == "self@example.com"


@pytest.mark.asyncio
async def test_get_user_admin_access(pg_connection, api_client, jwt_access_token: Callable[[UUID], str]) -> None:
    admin_id = uuid7()
    target_id = uuid7()
    await _insert_user(pg_connection, admin_id, "admin@example.com", status="admin")
    await _insert_user(pg_connection, target_id, "target@example.com")
    token = jwt_access_token(admin_id)

    response = await api_client.get(
        f"/public/v1/users/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == str(target_id)


@pytest.mark.asyncio
async def test_get_user_non_admin_access_other_returns_403(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    user_id = uuid7()
    other_id = uuid7()
    await _insert_user(pg_connection, user_id, "user1@example.com")
    await _insert_user(pg_connection, other_id, "user2@example.com")
    token = jwt_access_token(user_id)

    response = await api_client.get(
        f"/public/v1/users/{other_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_not_found_returns_400(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    admin_id = uuid7()
    await _insert_user(pg_connection, admin_id, "admin2@example.com", status="admin")
    token = jwt_access_token(admin_id)

    response = await api_client.get(
        f"/public/v1/users/{uuid7()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_users_admin_returns_all(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    admin_id = uuid7()
    other_id = uuid7()
    await _insert_user(pg_connection, admin_id, "listadmin@example.com", status="admin")
    await _insert_user(pg_connection, other_id, "listother@example.com")
    token = jwt_access_token(admin_id)

    response = await api_client.get(
        "/public/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 2
    assert isinstance(body["results"], list)


@pytest.mark.asyncio
async def test_list_users_self_only_filter(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    user_id = uuid7()
    await _insert_user(pg_connection, user_id, "selfonly@example.com")
    token = jwt_access_token(user_id)

    response = await api_client.get(
        "/public/v1/users",
        params={"user_id": str(user_id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_list_users_non_admin_without_filter_returns_403(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    user_id = uuid7()
    await _insert_user(pg_connection, user_id, "nofilter@example.com")
    token = jwt_access_token(user_id)

    response = await api_client.get(
        "/public/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_version_self_access(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    user_id = uuid7()
    await _insert_user(pg_connection, user_id, "versioned@example.com")
    await _insert_version(pg_connection, user_id, "versioned@example.com", version=1)
    token = jwt_access_token(user_id)

    response = await api_client.get(
        f"/public/v1/users/{user_id}/versions/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(user_id)
    assert body["version"] == 1
    assert body["event"] == "created"


@pytest.mark.asyncio
async def test_get_user_version_not_found_returns_400(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    user_id = uuid7()
    await _insert_user(pg_connection, user_id, "noversion@example.com")
    token = jwt_access_token(user_id)

    response = await api_client.get(
        f"/public/v1/users/{user_id}/versions/99",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_user_versions_self_access(
    pg_connection, api_client, jwt_access_token: Callable[[UUID], str]
) -> None:
    user_id = uuid7()
    await _insert_user(pg_connection, user_id, "listver@example.com")
    await _insert_version(pg_connection, user_id, "listver@example.com", version=1)
    token = jwt_access_token(user_id)

    response = await api_client.get(
        f"/public/v1/users/{user_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["user_id"] == str(user_id)
