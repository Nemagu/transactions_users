from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from application.errors import (
    AppError,
    AppInternalError,
    AppNotFoundError,
)
from domain.errors import DomainError, EntityPolicyError


def setup_error_handler(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request.state.error_context = {
            "detail": exc.msg,
            "action": exc.action,
            "struct_name": None,
            "data": exc.data,
        }
        content = {
            "detail": exc.msg,
            "data": exc.data,
        }
        if isinstance(exc, AppInternalError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif isinstance(exc, AppNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        return JSONResponse(status_code=status_code, content=jsonable_encoder(content))

    @app.exception_handler(DomainError)
    async def handle_domain_error(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        request.state.error_context = {
            "detail": exc.msg,
            "action": None,
            "struct_name": exc.struct_name,
            "data": exc.data,
        }
        content = {
            "detail": exc.msg,
            "data": exc.data,
        }
        if isinstance(exc, EntityPolicyError):
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        return JSONResponse(status_code=status_code, content=jsonable_encoder(content))
