from pathlib import Path

import pytest

from app.providers import base, youtube_music


def test_parse_duration() -> None:
    assert youtube_music._parse_duration("3:45") == 225_000
    assert youtube_music._parse_duration("1:02:03") == 3_723_000
    assert youtube_music._parse_duration(180) == 180_000
    assert youtube_music._parse_duration(None) is None
    assert youtube_music._parse_duration("") is None
    assert youtube_music._parse_duration("garbage") is None


def test_map_song() -> None:
    raw = {
        "videoId": "abc123",
        "title": "Blinding Lights",
        "artists": [{"name": "The Weeknd"}],
        "album": {"name": "After Hours"},
        "duration": "3:20",
        "thumbnails": [{"url": "small"}, {"url": "big"}],
        "isExplicit": True,
    }

    candidate = youtube_music._map_song(raw)

    assert candidate is not None
    assert candidate.source_id == "abc123"
    assert candidate.title == "Blinding Lights"
    assert candidate.artist == "The Weeknd"
    assert candidate.album == "After Hours"
    assert candidate.duration_ms == 200_000
    assert candidate.cover_url == "big"
    assert candidate.explicit is True


def test_map_song_skips_missing_video_id() -> None:
    assert youtube_music._map_song({"title": "No id"}) is None


async def test_search_maps_and_returns_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def search(self, *args: object, **kwargs: object) -> list[dict[str, object]]:
            return [
                {"videoId": "v1", "title": "T", "artists": [{"name": "A"}]},
                {"title": "no id"},
            ]

    provider = youtube_music.YouTubeMusicProvider()
    provider._client = FakeClient()

    results = await provider.search("hello")

    assert [r.source_id for r in results] == ["v1"]


async def test_find_source_returns_same_video_id() -> None:
    provider = youtube_music.YouTubeMusicProvider()
    candidate = base.TrackCandidate(provider="x", source_id="v1", title="T", artist="A")

    source = await provider.find_source(candidate)

    assert source is not None
    assert source.provider == "youtube_music"
    assert source.source_id == "v1"


async def test_resolve_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        youtube_music,
        "_ytdlp_extract_stream",
        lambda _source_id: base.StreamInfo(url="https://stream/1", ext="m4a"),
    )
    provider = youtube_music.YouTubeMusicProvider()

    stream = await provider.resolve_stream(
        base.AudioSource(provider="youtube_music", source_id="v1")
    )

    assert stream.url == "https://stream/1"


async def test_download(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        youtube_music,
        "_ytdlp_download",
        lambda _source_id, dest_dir: dest_dir / "v1.m4a",
    )
    provider = youtube_music.YouTubeMusicProvider()

    path = await provider.download(
        base.AudioSource(provider="youtube_music", source_id="v1"), tmp_path
    )

    assert path == tmp_path / "v1.m4a"
