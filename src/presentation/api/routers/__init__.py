from fastapi import APIRouter

from presentation.api.routers.health import health_router
from presentation.api.routers.public.v1 import v1_router

main_router = APIRouter()

main_router.include_router(health_router, prefix="/health")
main_router.include_router(v1_router, prefix="/public")
