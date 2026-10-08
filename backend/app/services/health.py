import asyncio
from collections.abc import Coroutine
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.redis import redis_client
from app.db.session import engine

CheckStatus = Literal["ok", "error"]


class HealthReport(BaseModel):
    status: CheckStatus
    database: CheckStatus
    redis: CheckStatus


async def _check_database() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _check_redis() -> None:
    await redis_client.ping()


async def _run(check: Coroutine[Any, Any, None]) -> CheckStatus:
    try:
        async with asyncio.timeout(get_settings().health_timeout_seconds):
            await check
    except Exception:
        return "error"
    return "ok"


async def check_health() -> HealthReport:
    db, rds = await asyncio.gather(_run(_check_database()), _run(_check_redis()))
    overall: CheckStatus = "ok" if db == "ok" and rds == "ok" else "error"
    return HealthReport(status=overall, database=db, redis=rds)
