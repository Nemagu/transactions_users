from typing import Any

__all__ = ["AppError", "AppInternalError", "AppInvalidDataError", "AppNotFoundError"]


class AppError(Exception):
    def __init__(
        self,
        msg: str,
        action: str,
        data: dict[str, Any] | None = None,
        *args: object,
    ) -> None:
        super().__init__(msg, *args)
        self.msg = msg
        self.action = action
        self.data = data or {}


class AppNotFoundError(AppError):
    pass


class AppInvalidDataError(AppError):
    pass


class AppInternalError(AppError):
    def __init__(
        self,
        msg: str,
        action: str,
        data: dict[str, Any] | None = None,
        wrap_error: BaseException | None = None,
    ) -> None:
        super().__init__(msg, action, data=data)
        self.wrap_error = wrap_error
