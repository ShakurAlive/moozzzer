"""Provider interfaces and shared models (stage 4.1).

A *metadata* provider turns a search query into normalized ``TrackCandidate``s.
An *audio* provider turns a candidate into a playable stream or a downloaded
file. The two libraries we rely on (ytmusicapi, yt-dlp) are synchronous, so
provider methods are async and offload blocking work with ``asyncio.to_thread``.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ProviderError(Exception):
    """A provider could not fulfil a request (bad id, network, no results)."""


class TrackCandidate(BaseModel):
    """Metadata search result, normalized across providers."""

    provider: str
    source_id: str
    title: str
    artist: str
    album: str | None = None
    duration_ms: int | None = None
    cover_url: str | None = None
    isrc: str | None = None
    explicit: bool = False


class AudioSource(BaseModel):
    """A resolvable audio source found for a candidate."""

    provider: str
    source_id: str
    title: str | None = None
    duration_ms: int | None = None


class StreamInfo(BaseModel):
    """A ready-to-play stream URL (plus any required request headers)."""

    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    ext: str | None = None


@runtime_checkable
class MetadataProvider(Protocol):
    name: str

    async def search(self, query: str, limit: int = 20) -> list[TrackCandidate]: ...


@runtime_checkable
class AudioProvider(Protocol):
    name: str

    async def find_source(self, candidate: TrackCandidate) -> AudioSource | None: ...
    async def resolve_stream(self, source: AudioSource) -> StreamInfo: ...
    async def download(self, source: AudioSource, dest_dir: Path) -> Path: ...
