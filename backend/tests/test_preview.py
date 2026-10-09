import pytest

from app.core.errors import AppError
from app.providers import base
from app.services import preview as preview_service


def test_validate_source_id() -> None:
    preview_service._validate("youtube_music", "dQw4w9WgXcQ")  # valid video id

    with pytest.raises(AppError):
        preview_service._validate("youtube_music", "https://evil.com")

    with pytest.raises(AppError):
        preview_service._validate("unknown", "whatever")


async def test_resolve_stream_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    class FakeAudio:
        name = "youtube_music"

        async def resolve_stream(self, source: base.AudioSource) -> base.StreamInfo:
            calls.append(1)
            return base.StreamInfo(url="https://stream/1", ext="m4a")

    monkeypatch.setattr(preview_service.registry, "enabled_audio", lambda: [FakeAudio()])

    first = await preview_service.resolve_stream("youtube_music", "dQw4w9WgXcQ")
    second = await preview_service.resolve_stream("youtube_music", "dQw4w9WgXcQ")

    assert first.url == "https://stream/1"
    assert second.url == "https://stream/1"
    assert len(calls) == 1


async def test_resolve_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preview_service.registry, "enabled_audio", lambda: [])

    with pytest.raises(AppError):
        await preview_service.resolve_stream("unknown", "whatever")
