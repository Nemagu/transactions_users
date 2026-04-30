from logging import getLogger
from time import perf_counter
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = perf_counter()
        try:
            response = await call_next(request)
        except BaseException as err:
            duration_ms = round((perf_counter() - start_time) * 1000, 2)
            context = self._build_context(
                request=request,
                status_code=None,
                duration_ms=duration_ms,
            )
            context["unhandled_error"] = str(err)
            logger.exception("http_request %s", context)
            raise

        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        context = self._build_context(
            request=request,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        if response.status_code >= 500:
            logger.error("http_request %s", context)
        elif response.status_code >= 400:
            logger.warning("http_request %s", context)
        else:
            logger.info("http_request %s", context)
        return response

    @staticmethod
    def _build_context(
        request: Request, status_code: int | None, duration_ms: float
    ) -> dict[str, Any]:
        error_context = getattr(request.state, "error_context", None)
        if not isinstance(error_context, dict):
            error_context = {}

        struct_name = error_context.get("struct_name")
        action = error_context.get("action")
        return {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "action": action,
            "struct_name": struct_name,
            "detail": error_context.get("detail"),
            "data": error_context.get("data"),
        }
