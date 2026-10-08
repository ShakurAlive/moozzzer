from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Connection, inspect
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.db import models  # noqa: F401
from app.db.base import Base
from tests.conftest import TEST_DATABASE_URL, run_alembic


def _tables(conn: Connection) -> set[str]:
    return set(inspect(conn).get_table_names()) - {"alembic_version"}


def _diff(conn: Connection) -> list[object]:
    ctx = MigrationContext.configure(conn, opts={"compare_type": True})
    return list(compare_metadata(ctx, Base.metadata))


async def test_downgrade_base_and_upgrade_head() -> None:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    try:
        await run_alembic("downgrade", "base")
        async with engine.connect() as conn:
            assert await conn.run_sync(_tables) == set()

        await run_alembic("upgrade", "head")
        async with engine.connect() as conn:
            assert await conn.run_sync(_tables) == set(Base.metadata.tables)
    finally:
        await engine.dispose()


async def test_models_match_migrations() -> None:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            assert await conn.run_sync(_diff) == []
    finally:
        await engine.dispose()
