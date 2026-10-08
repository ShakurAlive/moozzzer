from typing import Any, ClassVar

from arq.connections import RedisSettings

from app.core.config import get_settings


async def ping(_ctx: dict[str, Any]) -> str:
    return "pong"


class WorkerSettings:
    functions: ClassVar[list[Any]] = [ping]
    redis_settings = RedisSettings.from_dsn(str(get_settings().redis_url))
    # Server has 2 vCPU; audio conversion is CPU-bound.
    max_jobs = 2
    # Read by `arq --check` in the container healthcheck.
    health_check_interval = 60
