from typing import Any


class DomainError(Exception):
    def __init__(
        self,
        msg: str,
        struct_name: str,
        data: dict[str, Any] | None = None,
        *args: object,
    ) -> None:
        super().__init__(msg, *args)
        self.msg = msg
        self.struct_name = struct_name
        self.data = data or {}


class ValueObjectError(DomainError):
    pass


class ValueObjectInvalidDataError(ValueObjectError):
    pass


class EntityError(DomainError):
    pass


class EntityInvalidDataError(EntityError):
    pass


class EntityVersionLessThenCurrentError(EntityError):
    pass


class EntityIdempotentError(EntityError):
    pass


class EntityPolicyError(EntityError):
    pass


class EntityAlreadyExistsError(EntityError):
    pass
