"""SoundCloud audio provider (stage 4.6).

Audio only — no metadata search. Follows the YouTube Music reference in
structure: a blocking yt-dlp call wrapped in ``asyncio.to_thread``, with a
monkeypatchable module-level helper for tests. ``find_source`` searches
SoundCloud via yt-dlp's ``scsearch`` extractor using the candidate's
artist + title.
"""

import asyncio
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from app.providers import base

_YTDLP_OPTS: dict[str, object] = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "format": "bestaudio/best",
}


def _sc_search_first(query: str) -> Any | None:
    """First SoundCloud search hit for ``query``, or None if there are no results."""
    with YoutubeDL(_YTDLP_OPTS) as ydl:
        result = ydl.extract_info(f"scsearch1:{query}", download=False)
    if not isinstance(result, dict):
        return None
    entries = result.get("entries") or []
    if not entries:
        return None
    return entries[0]


def _stream_from_info(info: Any) -> base.StreamInfo:
    raw_headers = info.get("http_headers") or {}
    return base.StreamInfo(
        url=str(info["url"]),
        headers={str(k): str(v) for k, v in raw_headers.items()},
        ext=str(info["ext"]) if info.get("ext") else None,
    )


def _sc_extract_stream(source_url: str) -> base.StreamInfo:
    with YoutubeDL(_YTDLP_OPTS) as ydl:
        info = ydl.extract_info(source_url, download=False)
    if info is None:
        raise base.ProviderError("soundcloud: no stream info")
    return _stream_from_info(info)


def _sc_download(source_url: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    opts = {**_YTDLP_OPTS, "outtmpl": str(dest_dir / "%(id)s.%(ext)s")}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(source_url, download=True)
    if info is None:
        raise base.ProviderError("soundcloud: download failed")
    return Path(ydl.prepare_filename(info))


class SoundCloudProvider:
    name = "soundcloud"

    async def find_source(self, candidate: base.TrackCandidate) -> base.AudioSource | None:
        query = f"{candidate.artist} {candidate.title}"
        entry = await asyncio.to_thread(_sc_search_first, query)
        if entry is None:
            return None

        url = entry.get("webpage_url")
        if not url:
            return None
        duration = entry.get("duration")

        return base.AudioSource(
            provider=self.name,
            source_id=str(url),
            title=str(entry.get("title")) if entry.get("title") else candidate.title,
            duration_ms=int(duration * 1000) if duration else None,
        )

    async def resolve_stream(self, source: base.AudioSource) -> base.StreamInfo:
        return await asyncio.to_thread(_sc_extract_stream, source.source_id)

    async def download(self, source: base.AudioSource, dest_dir: Path) -> Path:
        return await asyncio.to_thread(_sc_download, source.source_id, dest_dir)
