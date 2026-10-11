"""Audio tag extraction via mutagen (stage 3.2).

Kept in its own module so the admin-upload service stays small and tests can
monkeypatch :func:`extract` without touching the network or the filesystem.
mutagen is imported lazily (it is only needed when a file is actually uploaded).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Sanitized, format-derived file extension for an uploaded file. The final path
# never reuses the user's filename, so traversal is impossible.
_CODEC_BY_EXT: dict[str, str] = {
    "mp3": "mp3",
    "m4a": "aac",
    "mp4": "aac",
    "flac": "flac",
    "opus": "opus",
    "ogg": "vorbis",
    "wav": "pcm",
}


@dataclass(frozen=True, slots=True)
class AudioTags:
    title: str | None
    artist: str | None
    album: str | None
    duration_ms: int | None
    bitrate_kbps: int | None
    codec: str | None
    cover_bytes: bytes | None
    cover_mime: str | None


def _first(values: Any) -> str | None:
    """First element of a mutagen easy-tag list (a list of strings)."""
    if not values:
        return None
    first = values[0]
    if not first:
        return None
    return str(first).strip() or None


def _extension(audio: Any, fallback: str | None) -> str | None:
    name = type(audio).__name__.lower()
    if "mp3" in name:
        return "mp3"
    if "mp4" in name:
        return "m4a"
    if "flac" in name:
        return "flac"
    if "opus" in name:
        return "opus"
    if "ogg" in name:
        return "ogg"
    if "wav" in name or "wave" in name:
        return "wav"
    if fallback:
        ext = fallback.lstrip(".").lower()
        if ext in _CODEC_BY_EXT:
            return ext
    return None


def _extract_cover(audio: Any) -> tuple[bytes | None, str | None]:
    tags = getattr(audio, "tags", None)
    if tags is None:
        return None, None

    # MP3 (ID3): APIC frames.
    getall = getattr(tags, "getall", None)
    if callable(getall):
        for frame in getall("APIC:"):
            data = getattr(frame, "data", None)
            if data:
                return bytes(data), getattr(frame, "mime", None) or "image/jpeg"

    # MP4/M4A: covr atoms.
    if hasattr(tags, "get"):
        covers = tags.get("covr")
        if covers:
            data = bytes(covers[0])
            mime = "image/png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
            return data, mime

    # FLAC & friends: attached pictures.
    pictures = getattr(tags, "pictures", None)
    if pictures:
        data = getattr(pictures[0], "data", None)
        if data:
            return bytes(data), getattr(pictures[0], "mime", None) or "image/jpeg"

    return None, None


def extract(path: Path) -> AudioTags:
    """Read tags/metadata from an audio file. Raises ``ValueError`` if not audio."""
    from mutagen import File as MutagenFile  # local import: upload-only path

    audio: Any = MutagenFile(path, easy=True)
    if audio is None:
        raise ValueError("unrecognized audio format")

    info = getattr(audio, "info", None)
    length = getattr(info, "length", None)
    duration_ms = round(float(length) * 1000) if length is not None else None
    bitrate = getattr(info, "bitrate", None)
    bitrate_kbps = round(int(bitrate) / 1000) if bitrate is not None else None

    cover_bytes, cover_mime = _extract_cover(audio)

    ext = _extension(audio, path.suffix)
    return AudioTags(
        title=_first(audio.get("title")),
        artist=_first(audio.get("artist")),
        album=_first(audio.get("album")),
        duration_ms=duration_ms,
        bitrate_kbps=bitrate_kbps,
        codec=_CODEC_BY_EXT.get(ext) if ext else None,
        cover_bytes=cover_bytes,
        cover_mime=cover_mime,
    )
