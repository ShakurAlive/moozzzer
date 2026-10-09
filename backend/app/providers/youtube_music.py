"""YouTube Music provider — the reference implementation (stage 4.1).

Implements BOTH interfaces so the other providers (and Qwen) have a clean
sample to follow:

- ``MetadataProvider.search``        -> ytmusicapi (YouTube Music public search)
- ``AudioProvider.find_source``      -> trivial: the video id IS the audio source
- ``AudioProvider.resolve_stream``   -> yt-dlp (best audio stream URL)
- ``AudioProvider.download``         -> yt-dlp (download to ``dest_dir``)

Both libraries are synchronous, so every blocking call is offloaded with
``asyncio.to_thread``. Never pass a user-supplied URL to yt-dlp — only ids we
got from a provider (SSRF protection). The module-level ``_*`` helpers exist so
tests can monkeypatch them without touching the network.
"""

import asyncio
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

from app.providers import base

_YTDLP_OPTS: dict[str, object] = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "format": "bestaudio/best",
}


def _parse_duration(value: object) -> int | None:
    """ytmusicapi returns ``"m:ss"`` / ``"h:mm:ss"`` strings or int seconds."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value * 1000)  # seconds -> ms
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            parts = [int(part) for part in value.split(":")]
        except ValueError:
            return None
        seconds = 0
        for part in parts:
            seconds = seconds * 60 + part
        return seconds * 1000
    return None


def _map_song(raw: Any) -> base.TrackCandidate | None:
    """Map one ytmusicapi song result to a normalized candidate (None if unusable)."""
    video_id = raw.get("videoId")
    if not video_id:
        return None

    artists = raw.get("artists") or []
    artist = ", ".join(str(a.get("name")) for a in artists if a.get("name")) or "Unknown"

    album = raw.get("album")
    album_name = str(album.get("name")) if isinstance(album, dict) else None

    thumbnails = raw.get("thumbnails") or []
    cover_url = str(thumbnails[-1].get("url")) if thumbnails else None

    return base.TrackCandidate(
        provider="youtube_music",
        source_id=str(video_id),
        title=str(raw.get("title") or "Unknown"),
        artist=artist,
        album=album_name,
        duration_ms=_parse_duration(raw.get("duration")),
        cover_url=cover_url,
        explicit=bool(raw.get("isExplicit", False)),
    )


def _stream_from_info(info: Any) -> base.StreamInfo:
    raw_headers = info.get("http_headers") or {}
    return base.StreamInfo(
        url=str(info["url"]),
        headers={str(k): str(v) for k, v in raw_headers.items()},
        ext=str(info["ext"]) if info.get("ext") else None,
    )


def _ytdlp_extract_stream(source_id: str) -> base.StreamInfo:
    with YoutubeDL(_YTDLP_OPTS) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={source_id}", download=False)
    if info is None:
        raise base.ProviderError("youtube_music: no stream info")
    return _stream_from_info(info)


def _ytdlp_download(source_id: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    opts = {**_YTDLP_OPTS, "outtmpl": str(dest_dir / "%(id)s.%(ext)s")}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={source_id}", download=True)
    if info is None:
        raise base.ProviderError("youtube_music: download failed")
    return Path(ydl.prepare_filename(info))


class YouTubeMusicProvider:
    """Metadata + audio via YouTube Music. The reference provider."""

    name = "youtube_music"

    def __init__(self) -> None:
        self._client: YTMusic | None = None

    def _get_client(self) -> YTMusic:
        if self._client is None:
            self._client = YTMusic()
        return self._client

    async def search(self, query: str, limit: int = 20) -> list[base.TrackCandidate]:
        raw = await asyncio.to_thread(self._get_client().search, query, filter="songs", limit=limit)
        candidates = [_map_song(item) for item in raw]
        return [c for c in candidates if c is not None]

    async def find_source(self, candidate: base.TrackCandidate) -> base.AudioSource | None:
        # YouTube Music serves metadata and audio from the same video id.
        return base.AudioSource(
            provider=self.name,
            source_id=candidate.source_id,
            title=candidate.title,
            duration_ms=candidate.duration_ms,
        )

    async def resolve_stream(self, source: base.AudioSource) -> base.StreamInfo:
        return await asyncio.to_thread(_ytdlp_extract_stream, source.source_id)

    async def download(self, source: base.AudioSource, dest_dir: Path) -> Path:
        return await asyncio.to_thread(_ytdlp_download, source.source_id, dest_dir)
