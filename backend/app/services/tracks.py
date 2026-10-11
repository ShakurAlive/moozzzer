"""Shared track serialization: builds the client-facing DTO with signed URLs."""

import uuid

from pydantic import BaseModel, ConfigDict

from app.db.models import Track
from app.services import media


class TrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    artist: str
    album: str | None
    duration_ms: int | None
    explicit: bool
    cover_url: str | None
    media_url: str | None


def to_dto(track: Track) -> TrackOut:
    """Track -> DTO. ``media_url``/``cover_url`` are signed and short-lived."""
    return TrackOut(
        id=track.id,
        title=track.title,
        artist=track.artist,
        album=track.album,
        duration_ms=track.duration_ms,
        explicit=track.explicit,
        cover_url=media.cover_url(track.id) if track.cover_path else None,
        media_url=media.media_url(track.id) if track.file_path else None,
    )
