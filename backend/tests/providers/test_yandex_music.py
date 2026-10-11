from dataclasses import dataclass

import pytest

from app.providers import yandex_music


@dataclass
class Artist:
    name: str


@dataclass
class Album:
    title: str


@dataclass
class Track:
    id: int | None
    title: str
    artists: list
    albums: list
    duration_ms: int | None
    cover_uri: str | None


@dataclass
class Paged:
    results: list


@dataclass
class SearchResult:
    tracks: Paged


def _track(**overrides: object) -> Track:
    data = {
        "id": 12345,
        "title": "Blinding Lights",
        "artists": [Artist("The Weeknd")],
        "albums": [Album("After Hours")],
        "duration_ms": 200000,
        "cover_uri": "avatars.yandex.net/get-music-content/1/2",
    }
    return Track(**(data | overrides))


def test_map_track() -> None:
    candidate = yandex_music._map_track(_track())

    assert candidate is not None
    assert candidate.provider == "yandex_music"
    assert candidate.source_id == "12345"
    assert candidate.title == "Blinding Lights"
    assert candidate.artist == "The Weeknd"
    assert candidate.album == "After Hours"
    assert candidate.duration_ms == 200000
    assert candidate.cover_url == "https://avatars.yandex.net/get-music-content/1/2"


def test_map_track_skips_missing_id() -> None:
    assert yandex_music._map_track(_track(id=None)) is None


async def test_search(monkeypatch: pytest.MonkeyPatch) -> None:
    track = _track(id=1, title="T", artists=[], albums=[], duration_ms=1000, cover_uri=None)

    class FakeClient:
        def search(self, text: str, type_: str) -> SearchResult:
            return SearchResult(tracks=Paged(results=[track]))

    provider = yandex_music.YandexMusicProvider()
    provider._client = FakeClient()

    results = await provider.search("query")

    assert [r.source_id for r in results] == ["1"]
