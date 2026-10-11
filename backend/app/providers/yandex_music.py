"""Yandex Music metadata provider (unofficial, metadata only).

Yandex Music is DRM-protected — no audio is exposed, so this provider only
implements ``MetadataProvider`` (search). It uses the unofficial `yandex_music`
library, which needs a Yandex OAuth token (``YANDEX_MUSIC_TOKEN``).
"""

import asyncio
from typing import Any

from yandex_music import Client

from app.core.config import get_settings
from app.providers import base


def _map_track(track: Any) -> base.TrackCandidate | None:
    track_id = getattr(track, "id", None)
    if track_id is None:
        return None

    artists = getattr(track, "artists", None) or []
    artist = ", ".join(str(a.name) for a in artists if getattr(a, "name", None)) or "Unknown"

    albums = getattr(track, "albums", None) or []
    album = str(albums[0].title) if albums else None

    cover_uri = getattr(track, "cover_uri", None)
    cover_url = f"https://{cover_uri}" if cover_uri else None

    return base.TrackCandidate(
        provider="yandex_music",
        source_id=str(track_id),
        title=str(getattr(track, "title", None) or "Unknown"),
        artist=artist,
        album=album,
        duration_ms=int(getattr(track, "duration_ms", 0)) or None,
        cover_url=cover_url,
        isrc=None,
        explicit=bool(getattr(track, "explicit", False)),
    )


class YandexMusicProvider:
    """Metadata search via Yandex Music (needs ``YANDEX_MUSIC_TOKEN``)."""

    name = "yandex_music"

    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is None:
            token = get_settings().yandex_music_token
            if not token:
                raise base.ProviderError("yandex_music: YANDEX_MUSIC_TOKEN is not set")
            self._client = Client(token)
        return self._client

    async def search(self, query: str, limit: int = 20) -> list[base.TrackCandidate]:
        raw = await asyncio.to_thread(self._get_client().search, query, type_="track")
        paged = getattr(raw, "tracks", None)
        results = getattr(paged, "results", None) or []
        candidates = [_map_track(track) for track in results[:limit]]
        return [c for c in candidates if c is not None]
