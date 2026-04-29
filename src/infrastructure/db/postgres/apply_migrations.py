from pathlib import Path

from yoyo import get_backend, read_migrations

from infrastructure.config import PostgresSettings


def apply_migrations(settings: PostgresSettings):

    migrations_dir = Path(__file__).parents[0] / "migrations"
    backend = get_backend(settings.url_with_psycopg)
    migrations = read_migrations(str(migrations_dir))
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
