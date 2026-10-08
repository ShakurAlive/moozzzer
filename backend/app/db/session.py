from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def create_engine() -> AsyncEngine:
    return create_async_engine(
        str(get_settings().database_url),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )


engine = create_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
