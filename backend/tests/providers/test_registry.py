import pytest

from app.providers import base, registry


def test_keys_parsing() -> None:
    assert registry._keys("a, b ,c") == ["a", "b", "c"]
    assert registry._keys("") == []
    assert registry._keys("  youtube_music  ") == ["youtube_music"]


async def test_search_isolates_provider_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    class Good:
        name = "good"

        async def search(self, query: str, limit: int = 20) -> list[base.TrackCandidate]:
            return [base.TrackCandidate(provider="good", source_id="1", title="T", artist="A")]

    class Bad:
        name = "bad"

        async def search(self, query: str, limit: int = 20) -> list[base.TrackCandidate]:
            raise RuntimeError("boom")

    monkeypatch.setattr(registry, "enabled_metadata", lambda: [Good(), Bad()])

    results = await registry.search("isolation")

    assert [r.source_id for r in results] == ["1"]


async def test_search_caches_results(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    class Fake:
        name = "fake"

        async def search(self, query: str, limit: int = 20) -> list[base.TrackCandidate]:
            calls.append(1)
            return [base.TrackCandidate(provider="fake", source_id="1", title="T", artist="A")]

    monkeypatch.setattr(registry, "enabled_metadata", lambda: [Fake()])

    await registry.search("cache-me")
    await registry.search("cache-me")

    assert len(calls) == 1
