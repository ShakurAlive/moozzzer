from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services import track_lifecycle


async def ping(_ctx: dict[str, Any]) -> str:
    return "pong"


async def gc_media(_ctx: dict[str, Any]) -> dict[str, int]:
    """Nightly job (stage 3.6): reconcile orphans, collect garbage, unlink files."""
    settings = get_settings()
    older_than = datetime.now(UTC) - timedelta(days=settings.gc_grace_days)

    async with SessionLocal() as session:
        try:
            reconciled = await track_lifecycle.reconcile_orphans(session)
            garbage = await track_lifecycle.collect_garbage(session, older_than)
            await session.commit()
        except BaseException:
            await session.rollback()
            raise

    root = Path(settings.media_root)
    for item in garbage:
        for relpath in (item.file_path, item.cover_path):
            if relpath:
                (root / relpath).unlink(missing_ok=True)

    return {"reconciled": reconciled, "collected": len(garbage)}


class WorkerSettings:
    functions: ClassVar[list[Any]] = [ping, gc_media]
    cron_jobs: ClassVar[list[Any]] = [cron(gc_media, hour=3, minute=30)]
    redis_settings = RedisSettings.from_dsn(str(get_settings().redis_url))
    # Server has 2 vCPU; audio conversion is CPU-bound.
    max_jobs = 2
    # Read by `arq --check` in the container healthcheck.
    health_check_interval = 60
