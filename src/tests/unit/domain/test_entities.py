import pytest

from domain.entities import Entity, EntityWithState
from domain.errors import EntityIdempotentError, EntityInvalidDataError
from domain.value_objects import AggregateName, State, Version


class DummyEntity(Entity):
    @property
    def entity_id(self) -> str:
        return self._entity_id

    def __init__(self, version: int = 1) -> None:
        super().__init__(
            version=Version(version),
            aggregate_name=AggregateName("dummy"),
            id_private_field="_entity_id",
            extend_repr_fields=["_entity_id", "_name"],
        )
        self._entity_id = "id-1"
        self._name = "name"


class DummyEntityWithState(EntityWithState):
    @property
    def entity_id(self) -> str:
        return self._entity_id

    def __init__(self, state: State = State.ACTIVE, version: int = 1) -> None:
        super().__init__(
            state=state,
            version=Version(version),
            aggregate_name=AggregateName("dummy_state"),
            id_private_field="_entity_id",
            extend_repr_fields=["_entity_id"],
        )
        self._entity_id = "id-2"


def test_entity_exposes_base_properties() -> None:
    entity = DummyEntity(version=3)

    assert entity.version.version == 3
    assert entity.original_version.version == 3
    assert entity.aggregate_name.name == "dummy"


def test_entity_mark_persisted_updates_original_version() -> None:
    entity = DummyEntity(version=1)

    entity._update_version()
    entity.mark_persisted()

    assert entity.original_version.version == 2


def test_entity_repr_and_str_include_fields() -> None:
    entity = DummyEntity(version=1)

    rendered = repr(entity)

    assert "_version" in rendered
    assert "_aggregate_name" in rendered
    assert "_entity_id" in rendered
    assert str(entity) == rendered


def test_entity_with_state_new_state_updates_version() -> None:
    entity = DummyEntityWithState(state=State.ACTIVE, version=1)

    entity.new_state(State.DELETED)

    assert entity.state == State.DELETED
    assert entity.version.version == 2


@pytest.mark.parametrize(
    ("method_name", "state"),
    [("new_state", State.ACTIVE), ("activate", State.ACTIVE), ("delete", State.DELETED)],
    ids=["new-state-same", "activate-active", "delete-deleted"],
)
def test_entity_with_state_idempotent_methods_raise(
    method_name: str, state: State
) -> None:
    entity = DummyEntityWithState(state=state)

    with pytest.raises(EntityIdempotentError):
        if method_name == "new_state":
            entity.new_state(state)
        else:
            getattr(entity, method_name)()


def test_entity_with_state_activate_and_delete() -> None:
    entity = DummyEntityWithState(state=State.DELETED, version=1)

    entity.activate()
    assert entity.state == State.ACTIVE
    assert entity.version.version == 2

    entity.mark_persisted()
    entity.delete()
    assert entity.state == State.DELETED
    assert entity.version.version == 3


def test_entity_with_state_check_state_raises_for_deleted() -> None:
    entity = DummyEntityWithState(state=State.DELETED)

    with pytest.raises(EntityInvalidDataError):
        entity._check_state("denied")


def test_entity_with_state_check_state_passes_for_active() -> None:
    entity = DummyEntityWithState(state=State.ACTIVE)

    entity._check_state("ok")
