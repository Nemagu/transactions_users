from fastapi import APIRouter

from presentation.api.routers.public.v1.user import user_router

v1_router = APIRouter(prefix="/v1", tags=["V1"])
v1_router.include_router(user_router)
