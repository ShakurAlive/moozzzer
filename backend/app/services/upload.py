"""Admin manual upload (stage 3.2).

Reads an uploaded audio file with mutagen, writes it under
``MEDIA_ROOT/{aa}/{uuid}.{ext}`` (plus the embedded cover, if any), and creates a
ready ``Track`` row with ``source_provider = "upload"``. The file is written
before the row is committed; on failure the partial files are removed.
"""

import asyncio
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.enums import TrackStatus
from app.db.models import Track
from app.services import audio_tags, media, tracks
from app.services.tracks import TrackOut

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB sanity cap for a family server
ALLOWED_EXTENSIONS = {"mp3", "m4a", "mp4", "flac", "opus", "ogg", "wav"}
_COVER_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _cover_ext(mime: str | None) -> str:
    return _COVER_EXT.get(mime or "", "jpg")


async def upload_track(session: AsyncSession, file: UploadFile) -> TrackOut:
    data = await file.read()
    if not data:
        raise AppError(400, "empty_file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise AppError(413, "file_too_large")

    track_id = uuid.uuid4()
    written: list[str] = []
    try:
        # mutagen needs a real path — write to a temporary file first.
        root = Path(get_settings().media_root)
        await asyncio.to_thread(root.mkdir, parents=True, exist_ok=True)
        tmp = root / f".tmp-{track_id.hex}{Path(file.filename or 'audio').suffix}"
        await asyncio.to_thread(tmp.write_bytes, data)
        try:
            try:
                tags = await asyncio.to_thread(audio_tags.extract, tmp)
            except ValueError as exc:
                raise AppError(415, "unsupported_media_type") from exc
            ext = _extension(tags, tmp.suffix, file.filename)
        finally:
            await asyncio.to_thread(tmp.unlink, missing_ok=True)

        if ext is None or ext not in ALLOWED_EXTENSIONS:
            raise AppError(415, "unsupported_media_type")

        audio_rel = media.audio_relpath(track_id, ext)
        await asyncio.to_thread(media.write_atomic, audio_rel, data)
        written.append(audio_rel)

        cover_rel: str | None = None
        if tags.cover_bytes is not None:
            cover_rel = media.cover_relpath(track_id, _cover_ext(tags.cover_mime))
            await asyncio.to_thread(media.write_atomic, cover_rel, tags.cover_bytes)
            written.append(cover_rel)

        track = Track(
            id=track_id,
            title=tags.title or "Unknown",
            artist=tags.artist or "Unknown",
            album=tags.album,
            duration_ms=tags.duration_ms,
            explicit=False,
            source_provider="upload",
            source_id=uuid.uuid4().hex,
            file_path=audio_rel,
            file_size=len(data),
            codec=tags.codec,
            bitrate_kbps=tags.bitrate_kbps,
            cover_path=cover_rel,
            status=TrackStatus.READY,
        )
        session.add(track)
        await session.commit()
    except Exception:
        await session.rollback()
        root = Path(get_settings().media_root)
        for relpath in written:
            await asyncio.to_thread((root / relpath).unlink, missing_ok=True)
        raise

    return tracks.to_dto(track)


def _extension(tags: audio_tags.AudioTags, tmp_suffix: str, filename: str | None) -> str | None:
    """Prefer the mutagen-detected format, then fall back to the file extension."""
    if tags.codec in {"mp3", "flac", "opus", "aac", "vorbis", "pcm"}:
        return {  # codec -> file extension
            "mp3": "mp3",
            "aac": "m4a",
            "flac": "flac",
            "opus": "opus",
            "vorbis": "ogg",
            "pcm": "wav",
        }[tags.codec]
    for source in (tmp_suffix, filename or ""):
        ext = Path(source).suffix.lstrip(".").lower()
        if ext in ALLOWED_EXTENSIONS:
            return ext
    return None
