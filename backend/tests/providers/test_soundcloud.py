from pathlib import Path

import pytest

from app.providers import base, soundcloud


async def test_find_source_maps_first_result(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_search(query: str) -> dict[str, object] | None:
        return {
            "webpage_url": "https://soundcloud.com/a/b",
            "title": "Track",
            "duration": 180.5,
        }

    monkeypatch.setattr(soundcloud, "_sc_search_first", fake_search)
    provider = soundcloud.SoundCloudProvider()
    candidate = base.TrackCandidate(provider="x", source_id="1", title="Track", artist="Artist")

    source = await provider.find_source(candidate)

    assert source is not None
    assert source.provider == "soundcloud"
    assert source.source_id == "https://soundcloud.com/a/b"
    assert source.duration_ms == 180_500


async def test_find_source_returns_none_when_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(soundcloud, "_sc_search_first", lambda _query: None)
    provider = soundcloud.SoundCloudProvider()

    source = await provider.find_source(
        base.TrackCandidate(provider="x", source_id="1", title="T", artist="A")
    )

    assert source is None


async def test_resolve_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        soundcloud,
        "_sc_extract_stream",
        lambda _url: base.StreamInfo(url="https://stream/2", ext="mp3"),
    )
    provider = soundcloud.SoundCloudProvider()

    stream = await provider.resolve_stream(
        base.AudioSource(provider="soundcloud", source_id="https://sc/a")
    )

    assert stream.url == "https://stream/2"


async def test_download(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        soundcloud,
        "_sc_download",
        lambda _url, dest_dir: dest_dir / "track.mp3",
    )
    provider = soundcloud.SoundCloudProvider()

    path = await provider.download(
        base.AudioSource(provider="soundcloud", source_id="https://sc/a"), tmp_path
    )

    assert path == tmp_path / "track.mp3"
