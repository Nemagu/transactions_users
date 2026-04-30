import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class PerformanceMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Process-Time",
        header_name_ms: str = "X-Process-Time-MS",
    ):
        super().__init__(app)
        self.header_name = header_name
        self.header_name_ms = header_name_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        process_time_ms = round(process_time * 1000, 2)

        response.headers[self.header_name] = str(process_time)
        response.headers[self.header_name_ms] = str(process_time_ms)

        return response
