import pytest
from httpx import AsyncClient

from app.services import health as health_service


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/api/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok", "redis": "ok"}


async def test_health_reports_redis_failure(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken() -> None:
        raise ConnectionError("redis down")

    monkeypatch.setattr(health_service, "_check_redis", broken)

    resp = await client.get("/api/health")

    assert resp.status_code == 503
    assert resp.json() == {"status": "error", "database": "ok", "redis": "error"}
