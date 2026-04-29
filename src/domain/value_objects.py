from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from domain.errors import ValueObjectInvalidDataError


@dataclass(frozen=True)
class Version:
    version: int

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueObjectInvalidDataError(
                msg="версия не может быть меньше 1",
                struct_name="версия агрегата",
                data={"version": self.version},
            )


@dataclass(frozen=True)
class AggregateName:
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self.name.strip())
        name_len = len(self.name)
        if name_len == 0:
            raise ValueObjectInvalidDataError(
                msg="название агрегата не может быть пустым",
                struct_name="название агрегата",
                data={"aggregate_name": self.name},
            )
        if name_len > 50:
            raise ValueObjectInvalidDataError(
                msg="название агрегата не может содержать более 50 символов",
                struct_name="название агрегата",
                data={"aggregate_name": self.name},
            )


@dataclass(frozen=True)
class ProjectionName:
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self.name.strip())
        name_len = len(self.name)
        if name_len == 0:
            raise ValueObjectInvalidDataError(
                msg="название проекции не может быть пустым",
                struct_name="название проекции",
                data={"projection_name": self.name},
            )
        if name_len > 50:
            raise ValueObjectInvalidDataError(
                msg="название проекции не может содержать более 50 символов",
                struct_name="название проекции",
                data={"projection_name": self.name},
            )


class State(StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"

    def is_active(self) -> bool:
        return self == self.__class__.ACTIVE

    def is_deleted(self) -> bool:
        return self == self.__class__.DELETED

    @classmethod
    def from_str(cls, value: str) -> Self:
        lower_value = value.lower()
        if lower_value in cls._value2member_map_:
            return cls(lower_value)
        raise ValueObjectInvalidDataError(
            msg="не удалось найти состояние по предоставленной строке",
            struct_name="состояние агрегата",
            data={"state": value},
        )
