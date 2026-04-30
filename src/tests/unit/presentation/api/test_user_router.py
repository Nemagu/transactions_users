from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.dto.user import UserSimpleDTO
from presentation.api.dependencies import (
    db_unit_of_work,
    email_builder,
    email_sender,
    password_manager,
    randomizer,
    redis_store,
    user_id_extractor,
)
from presentation.api.routers.public.v1.user import user_router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(user_router)
    app.dependency_overrides[db_unit_of_work] = lambda: object()
    app.dependency_overrides[redis_store] = lambda: object()
    app.dependency_overrides[email_sender] = lambda: object()
    app.dependency_overrides[email_builder] = lambda: object()
    app.dependency_overrides[randomizer] = lambda: object()
    app.dependency_overrides[password_manager] = lambda: object()
    app.dependency_overrides[user_id_extractor] = lambda: uuid4()
    return TestClient(app)


def test_user_router_endpoints(monkeypatch):
    dto = UserSimpleDTO(
        user_id=uuid4(),
        email="user@example.com",
        status="user",
        state="active",
        version=1,
    )

    async def none_execute(self, command):
        return None

    async def dto_execute(self, command):
        return dto

    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.UserConfirmingEmailUseCase.execute",
        none_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.UserCreatingUseCase.execute",
        dto_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.AuthCodeSendingUseCase.execute",
        none_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.CodeAuthUseCase.execute",
        dto_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.PasswordAuthUseCase.execute",
        dto_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.NewEmailConfirmingUseCase.execute",
        none_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.UserEmailChangingUseCase.execute",
        dto_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.UserFreezingUseCase.execute",
        dto_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.UserAppointingAdminUseCase.execute",
        dto_execute,
    )
    monkeypatch.setattr(
        "presentation.api.routers.public.v1.user.UserAppointingUserUseCase.execute",
        dto_execute,
    )

    client = _build_client()
    user_id = str(uuid4())

    assert client.post("/users/confirm-email", json={"email": "u@example.com"}).status_code == 200
    assert (
        client.post(
            "/users", json={"email": "u@example.com", "code": 123456, "password": "pass"}
        ).status_code
        == 200
    )
    assert client.post("/users/auth/send-code", json={"email": "u@example.com"}).status_code == 200
    assert client.post("/users/auth/code", json={"email": "u@example.com", "code": 123456}).status_code == 200
    assert (
        client.post(
            "/users/auth/password", json={"email": "u@example.com", "password": "pass"}
        ).status_code
        == 200
    )
    assert client.post("/users/email/confirm-new", json={"new_email": "n@example.com"}).status_code == 200
    assert (
        client.put(
            "/users/email",
            json={"new_email": "n@example.com", "new_email_code": 111111, "old_email_code": 222222},
        ).status_code
        == 200
    )
    assert client.put(f"/users/{user_id}/freeze").status_code == 200
    assert client.put(f"/users/{user_id}/appoint-admin").status_code == 200
    assert client.put(f"/users/{user_id}/appoint-user").status_code == 200
