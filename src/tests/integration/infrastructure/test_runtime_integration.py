import pytest

from infrastructure.db.postgres.connection import PostgresConnectionManager
from infrastructure.masage_broker.nats.connection import NatsConnectionManager


@pytest.mark.asyncio
async def test_postgres_connection_manager_query(postgres_settings) -> None:
    manager = PostgresConnectionManager(postgres_settings)
    await manager.init()
    try:
        async with manager.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT COUNT(*) FROM users_tables")
                row = await cursor.fetchone()
        assert row is not None
        assert row["count"] >= 4
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_nats_connection_manager_connect(nats_settings) -> None:
    manager = NatsConnectionManager(nats_settings)
    try:
        nc, js = await manager.client_with_jetstream()
        account_info = await js.account_info()
        assert nc.is_connected is True
        assert account_info is not None
    finally:
        await manager.close()
