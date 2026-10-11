"""Tests for the admin manual upload endpoint (stage 3.2)."""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.services import audio_tags, media, upload
from app.services.audio_tags import AudioTags


def make_settings(root: Path) -> Settings:
    return Settings(media_signing_secret="s" * 32, media_root=str(root))


def _install(monkeypatch: pytest.MonkeyPatch, root: Path) -> Settings:
    settings = make_settings(root)
    monkeypatch.setattr(upload, "get_settings", lambda: settings)
    monkeypatch.setattr(media, "get_settings", lambda: settings)
    return settings


async def test_upload_track(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install(monkeypatch, tmp_path)
    tags = AudioTags(
        title="Song",
        artist="Artist",
        album="Album",
        duration_ms=200_000,
        bitrate_kbps=256,
        codec="mp3",
        cover_bytes=None,
        cover_mime=None,
    )
    monkeypatch.setattr(audio_tags, "extract", lambda path: tags)

    file = UploadFile(BytesIO(b"fake-mp3-data"), filename="song.mp3")
    result = await upload.upload_track(db_session, file)

    assert result.title == "Song"
    assert result.artist == "Artist"
    assert result.duration_ms == 200_000
    assert result.media_url is not None

    audio_path = tmp_path / result.id.hex[:2] / f"{result.id}.mp3"
    assert audio_path.read_bytes() == b"fake-mp3-data"


async def test_upload_writes_cover(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install(monkeypatch, tmp_path)
    tags = AudioTags(
        title="Song",
        artist="Artist",
        album=None,
        duration_ms=None,
        bitrate_kbps=None,
        codec="mp3",
        cover_bytes=b"\xff\xd8\xffcover",
        cover_mime="image/jpeg",
    )
    monkeypatch.setattr(audio_tags, "extract", lambda path: tags)

    file = UploadFile(BytesIO(b"data"), filename="song.mp3")
    result = await upload.upload_track(db_session, file)

    assert result.cover_url is not None
    cover_path = tmp_path / result.id.hex[:2] / f"{result.id}.cover.jpg"
    assert cover_path.read_bytes() == b"\xff\xd8\xffcover"


async def test_upload_rejects_non_audio(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install(monkeypatch, tmp_path)

    def fail(path: Path) -> AudioTags:
        raise ValueError("unrecognized audio format")

    monkeypatch.setattr(audio_tags, "extract", fail)

    file = UploadFile(BytesIO(b"not audio"), filename="x.txt")
    with pytest.raises(AppError) as exc:
        await upload.upload_track(db_session, file)

    assert exc.value.code == "unsupported_media_type"
