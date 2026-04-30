from importlib import import_module
from types import SimpleNamespace

migrations_module = import_module("infrastructure.db.postgres.apply_migrations")


class FakeLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeBackend:
    def __init__(self) -> None:
        self.applied = None

    def lock(self):
        return FakeLock()

    def to_apply(self, migrations):
        return migrations

    def apply_migrations(self, migrations):
        self.applied = migrations


def test_apply_migrations_calls_backend(monkeypatch) -> None:
    backend = FakeBackend()
    migrations = ["m1", "m2"]

    monkeypatch.setattr(migrations_module, "get_backend", lambda url: backend)
    monkeypatch.setattr(migrations_module, "read_migrations", lambda path: migrations)

    migrations_module.apply_migrations(
        SimpleNamespace(url_with_psycopg="postgresql+psycopg://x")
    )

    assert backend.applied == migrations
