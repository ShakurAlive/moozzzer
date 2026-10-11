"""Tests for mutagen tag extraction (stage 3.2), with a fake ``mutagen`` module."""

import sys
import types
from pathlib import Path

import pytest

from app.services import audio_tags


class _Info:
    length = 200.0
    bitrate = 256_000


class _EasyAudio:
    def __init__(self, path: str, easy: bool = False) -> None:
        self.info = _Info()
        self.tags = None

    def get(self, key: str, default: object = None) -> object:
        return {
            "title": ["Song"],
            "artist": ["Artist"],
            "album": [None],
        }.get(key, default)


def _install_fake_mutagen(monkeypatch: pytest.MonkeyPatch, file_factory) -> None:
    module = types.ModuleType("mutagen")
    module.File = file_factory  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mutagen", module)


def test_extract_text_tags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install_fake_mutagen(monkeypatch, _EasyAudio)
    path = tmp_path / "song.mp3"
    path.write_bytes(b"x")

    tags = audio_tags.extract(path)

    assert tags.title == "Song"
    assert tags.artist == "Artist"
    assert tags.album is None
    assert tags.duration_ms == 200_000
    assert tags.bitrate_kbps == 256
    assert tags.codec == "mp3"
    assert tags.cover_bytes is None


def test_extract_cover_from_mp4(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Mp4Audio(_EasyAudio):
        def __init__(self, path: str, easy: bool = False) -> None:
            super().__init__(path, easy)
            self.tags = types.SimpleNamespace(get=lambda key: [b"\x89PNG\r\n\x1a\n" + b"x"])

    _install_fake_mutagen(monkeypatch, Mp4Audio)
    path = tmp_path / "song.m4a"
    path.write_bytes(b"x")

    tags = audio_tags.extract(path)

    assert tags.cover_mime == "image/png"
    assert tags.cover_bytes is not None
    assert tags.codec == "aac"


def test_extract_unknown_format_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install_fake_mutagen(monkeypatch, lambda path, easy=False: None)
    path = tmp_path / "song.mp3"
    path.write_bytes(b"x")

    with pytest.raises(ValueError):
        audio_tags.extract(path)
