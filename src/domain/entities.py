from abc import ABC
from typing import Any

from domain.errors import EntityIdempotentError, EntityInvalidDataError
from domain.value_objects import AggregateName, State, Version


class Entity(ABC):
    def __init__(
        self,
        version: Version,
        aggregate_name: AggregateName,
        id_private_field: str,
        main_error_field_name: str | None = None,
        extend_repr_fields: list[str] | None = None,
    ) -> None:
        self._version = version
        self._original_version = version
        self._aggregate_name = aggregate_name
        self._str_fields = ["_version", "_aggregate_name"]
        if extend_repr_fields:
            self._str_fields.extend(extend_repr_fields)
        self._id_private_field = id_private_field
        self._id_error_field_name = id_private_field.replace("_", "", 1)
        if main_error_field_name:
            self._main_error_field_name = main_error_field_name
        else:
            self._main_error_field_name = id_private_field.split("_")[1]

    @property
    def version(self) -> Version:
        return self._version

    @property
    def original_version(self) -> Version:
        return self._original_version

    @property
    def aggregate_name(self) -> AggregateName:
        return self._aggregate_name

    def _update_version(self) -> None:
        if self._version == self._original_version:
            self._version = Version(self._original_version.version + 1)

    def _error_data(
        self, msg: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = data or dict()
        entity_id = getattr(self, self._id_error_field_name)
        id_value = getattr(entity_id, self._id_error_field_name, entity_id)
        data[self._id_error_field_name] = id_value
        return {
            "msg": msg,
            "struct_name": self._aggregate_name.name,
            "data": {self._main_error_field_name: data},
        }

    def mark_persisted(self) -> None:
        self._original_version = self._version

    def __repr__(self) -> str:
        fields = ""
        for field in self._str_fields:
            if fields:
                fields = f"{fields}, {field}: {getattr(self, field)}"
            else:
                fields = f"{field}: {getattr(self, field)}"
        return f"{self.__class__.__name__}({fields})"

    def __str__(self) -> str:
        return self.__repr__()


class EntityWithState(Entity):
    def __init__(
        self,
        state: State,
        version: Version,
        aggregate_name: AggregateName,
        id_private_field: str,
        main_error_field_name: str | None = None,
        extend_repr_fields: list[str] | None = None,
    ) -> None:
        extend_repr_fields = extend_repr_fields or list()
        extend_repr_fields.append("_state")
        super().__init__(
            version,
            aggregate_name,
            id_private_field,
            main_error_field_name,
            extend_repr_fields,
        )
        self._state = state

    @property
    def state(self) -> State:
        return self._state

    def new_state(self, state: State) -> None:
        if self._state == state:
            raise EntityIdempotentError(
                **self._error_data(
                    "новое состояние идентично текущему", {"state": state.value}
                )
            )
        self._state = state
        self._update_version()

    def activate(self) -> None:
        if self._state.is_active():
            raise EntityIdempotentError(
                **self._error_data(
                    f"{self._aggregate_name.name} уже активно",
                    {"state": self._state.value},
                )
            )
        self._state = self._state.__class__.ACTIVE
        self._update_version()

    def delete(self) -> None:
        if self._state.is_deleted():
            raise EntityIdempotentError(
                **self._error_data(
                    f"{self._aggregate_name.name} уже удалено",
                    {"state": self._state.value},
                )
            )
        self._state = self._state.__class__.DELETED
        self._update_version()

    def _check_state(self, msg: str, data: dict[str, Any] | None = None) -> None:
        data = data or dict()
        data["state"] = self._state.value
        if self._state.is_deleted():
            raise EntityInvalidDataError(**self._error_data(msg, data))
