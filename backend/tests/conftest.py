import asyncio
import os
import re
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _resolve_test_database_url() -> URL:
    """TEST_DATABASE_URL, or DATABASE_URL with "_test" appended to the database name."""
    explicit = os.environ.get("TEST_DATABASE_URL")
    url = make_url(explicit or str(Settings().database_url))
    if not explicit and url.database and not url.database.endswith("_test"):
        url = url.set(database=f"{url.database}_test")
    # The database is dropped on every run: refuse anything that is not clearly a test DB.
    if not re.fullmatch(r"[a-z0-9_]+_test", url.database or ""):
        raise RuntimeError(f"Refusing to use {url.database!r} as test database")
    return url


TEST_DATABASE_URL = _resolve_test_database_url()
# Must happen before anything imports app.db.session (it builds the engine at import time).
os.environ["DATABASE_URL"] = TEST_DATABASE_URL.render_as_string(hide_password=False)
get_settings.cache_clear()


def alembic_config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    return cfg


async def run_alembic(cmd: str, revision: str) -> None:
    # env.py calls asyncio.run(), so it needs a thread without a running loop.
    await asyncio.to_thread(getattr(command, cmd), alembic_config(), revision)


async def _recreate_test_database() -> None:
    admin = create_async_engine(
        TEST_DATABASE_URL.set(database="postgres"), isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    name = TEST_DATABASE_URL.database
    async with admin.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{name}"'))
    await admin.dispose()


@pytest.fixture(scope="session", autouse=True)
async def database() -> AsyncIterator[None]:
    """Fresh test database, migrated to head via Alembic (not create_all)."""
    await _recreate_test_database()
    await run_alembic("upgrade", "head")
    yield
    from app.db.session import engine

    await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Session inside an outer transaction that is rolled back after the test."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
