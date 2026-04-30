from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.errors import AppError, AppInternalError, AppNotFoundError
from domain.errors import DomainError, EntityPolicyError
from presentation.api.error_handler import setup_error_handler


def _make_client(error: Exception) -> TestClient:
    app = FastAPI()
    setup_error_handler(app)

    @app.get("/boom")
    async def boom() -> None:
        raise error

    return TestClient(app)


def test_app_internal_error_returns_500():
    client = _make_client(AppInternalError(msg="x", action="act"))

    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"detail": "x", "data": {}}


def test_app_not_found_error_returns_404():
    client = _make_client(AppNotFoundError(msg="x", action="act", data={"k": 1}))

    response = client.get("/boom")

    assert response.status_code == 404
    assert response.json() == {"detail": "x", "data": {"k": 1}}


def test_app_error_returns_400():
    client = _make_client(AppError(msg="x", action="act"))

    response = client.get("/boom")

    assert response.status_code == 400


def test_domain_policy_error_returns_403():
    client = _make_client(EntityPolicyError(msg="x", struct_name="User"))

    response = client.get("/boom")

    assert response.status_code == 403
    assert response.json() == {"detail": "x", "data": {}}


def test_domain_error_returns_400():
    client = _make_client(DomainError(msg="x", struct_name="User", data={"k": 1}))

    response = client.get("/boom")

    assert response.status_code == 400
    assert response.json() == {"detail": "x", "data": {"k": 1}}
