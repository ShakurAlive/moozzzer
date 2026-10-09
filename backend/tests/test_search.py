import pytest

from app.providers import base
from app.services import search as search_service


def _candidate(**overrides: object) -> base.TrackCandidate:
    data = {"provider": "x", "source_id": "1", "title": "T", "artist": "A"}
    return base.TrackCandidate(**(data | overrides))


def test_dedup_by_isrc() -> None:
    a = _candidate(provider="x", source_id="1", isrc="USUM72000001")
    b = _candidate(provider="y", source_id="2", isrc="USUM72000001")

    assert search_service._dedup([a, b]) == [a]


def test_dedup_by_artist_title_duration() -> None:
    a = _candidate(provider="x", source_id="1", duration_ms=200_000)
    b = _candidate(provider="y", source_id="2", duration_ms=202_000)

    assert search_service._dedup([a, b]) == [a]


def test_dedup_keeps_different_tracks() -> None:
    a = _candidate(provider="x", source_id="1", title="T", artist="A", duration_ms=200_000)
    b = _candidate(provider="x", source_id="2", title="U", artist="B", duration_ms=300_000)

    assert search_service._dedup([a, b]) == [a, b]


async def test_search_tracks_ranks_and_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search(query: str, limit: int = 20) -> list[base.TrackCandidate]:
        return [
            _candidate(source_id="1", title="other", cover_url="c"),
            _candidate(source_id="2", title="needle", duration_ms=1000),
        ]

    monkeypatch.setattr(search_service.registry, "search", fake_search)

    results = await search_service.search_tracks("needle", limit=10)

    assert [r.title for r in results] == ["needle", "other"]
