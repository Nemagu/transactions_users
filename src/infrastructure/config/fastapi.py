"""Модуль `infrastructure/config/fastapi.py` слоя инфраструктуры."""

from pydantic import BaseModel


class FastAPISettings(BaseModel):
    """Компонент `FastAPISettings`."""
    user_id_header_name: str = "x-user-id"
    request_id_header_name: str = "x-request-id"
    process_time_header_name: str = "x-process-time"
    process_time_ms_header_name: str = "x-process-time-ms"


class UvicornSettings(BaseModel):
    """Компонент `UvicornSettings`."""
    host: str = "localhost"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    loop: str = "uvloop"
