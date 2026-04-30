from fastapi import Request

from infrastructure.db.postgres import PostgresUnitOfWork


async def db_unit_of_work(request: Request) -> PostgresUnitOfWork:
    async with request.app.state.db_connection_manager.connection() as conn:
        return PostgresUnitOfWork(conn)
