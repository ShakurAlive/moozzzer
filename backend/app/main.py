from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.core.redis import redis_client
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await redis_client.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    is_prod = settings.app_env == "prod"
    app = FastAPI(
        title="Moozzzer API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url=None if is_prod else "/api/docs",
        redoc_url=None,
    )
    # /api/health stays unversioned for probes; business endpoints will live under /api/v1.
    app.include_router(api_router, prefix="/api")
    app.add_exception_handler(AppError, app_error_handler)
    return app


app = create_app()
