from fastapi import APIRouter

health_router = APIRouter(tags=["health"])


@health_router.get("")
def health_check() -> dict:
    return {"status": "ok"}
