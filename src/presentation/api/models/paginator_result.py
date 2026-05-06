from typing import Generic, TypeVar

from pydantic import BaseModel

__all__ = ["LimitOffsetPaginatorResult"]

T = TypeVar("T")


class LimitOffsetPaginatorResult(BaseModel, Generic[T]):
    """Результат запроса с пагинацией limit/offset."""

    count: int
    results: list[T]
