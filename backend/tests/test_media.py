"""Unit tests for media storage and signed URLs (stage 3.1)."""

import time
import uuid
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services import media


def make_settings(root: Path, *, ttl: int = 3600) -> Settings:
    return Settings(
        media_signing_secret="s" * 32,
        media_url_ttl_seconds=ttl,
        media_root=str(root),
    )


def test_shard_and_relpaths() -> None:
    track_id = uuid.UUID("00000000-0000-0000-0000-0000000000ab")

    assert media.shard_dir(track_id) == "00"
    assert media.audio_relpath(track_id, "MP3") == f"00/{track_id}.mp3"
    assert media.cover_relpath(track_id, "JPG") == f"00/{track_id}.cover.jpg"


def test_sign_and_verify_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(media, "get_settings", lambda: make_settings(tmp_path))
    track_id = uuid.uuid4()
    exp = str(int(time.time()) + 100)
    sig = media._sign(f"{track_id}:{exp}")

    assert media.verify(track_id, exp, sig) is True


def test_verify_rejects_expired(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(media, "get_settings", lambda: make_settings(tmp_path))
    track_id = uuid.uuid4()
    exp = str(int(time.time()) - 100)
    sig = media._sign(f"{track_id}:{exp}")

    assert media.verify(track_id, exp, sig) is False


def test_verify_rejects_tampered_signature(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(media, "get_settings", lambda: make_settings(tmp_path))
    track_id = uuid.uuid4()
    exp = str(int(time.time()) + 100)

    assert media.verify(track_id, exp, "0" * 64) is False
    assert media.verify(track_id, exp, "") is False


def test_signed_urls_contain_query(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(media, "get_settings", lambda: make_settings(tmp_path))
    track_id = uuid.uuid4()

    audio = media.media_url(track_id)
    cover = media.cover_url(track_id)

    assert audio.startswith(f"/api/v1/media/{track_id}?exp=")
    assert "&sig=" in audio
    assert cover.startswith(f"/api/v1/media/{track_id}/cover?exp=")
    assert "&sig=" in cover


def test_resolve_is_confined_to_media_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(media, "get_settings", lambda: make_settings(tmp_path))

    resolved = media.resolve("ab/song.mp3")
    assert resolved.parent.name == "ab"

    with pytest.raises(ValueError):
        media.resolve("../etc/passwd")


def test_write_atomic_and_guess_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(media, "get_settings", lambda: make_settings(tmp_path))

    path = media.write_atomic("ab/song.mp3", b"ID3-test")
    assert path.read_bytes() == b"ID3-test"
    assert media.guess_media_type(path) == "audio/mpeg"
