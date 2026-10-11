"""Signed media streaming (stage 3.1): audio with HTTP Range, and cover images.

``<audio>``/``<img>`` cannot send a Bearer header, so these endpoints authorize
via short-lived signed URLs (``?exp=&sig=``) instead. The signature is verified
before any database or filesystem access; the track's real path is then looked
up (paths are never exposed to clients). Starlette's ``FileResponse`` serves the
file and transparently handles ``Range: bytes=...`` requests.
"""

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.deps import SessionDep
from app.core.errors import AppError
from app.db.enums import TrackStatus
from app.db.models import Track
from app.services import media

router = APIRouter(prefix="/v1/media", tags=["media"])


async def _track_file_path(session: SessionDep, track_id: UUID) -> str:
    """DB-stored relative file path of a ready track (404 for anything else)."""
    track = await session.get(Track, track_id)
    if track is None or track.status is not TrackStatus.READY or not track.file_path:
        raise AppError(404, "track_not_found")
    return track.file_path


@router.get("/{track_id}")
async def stream_audio(track_id: UUID, exp: str, sig: str, session: SessionDep) -> FileResponse:
    if not media.verify(track_id, exp, sig):
        raise AppError(403, "invalid_media_url")
    path = media.resolve(await _track_file_path(session, track_id))
    if not path.is_file():
        raise AppError(404, "media_missing")
    return FileResponse(path, media_type=media.guess_media_type(path))


@router.get("/{track_id}/cover")
async def stream_cover(track_id: UUID, exp: str, sig: str, session: SessionDep) -> FileResponse:
    if not media.verify(track_id, exp, sig):
        raise AppError(403, "invalid_media_url")
    track = await session.get(Track, track_id)
    if track is None or not track.cover_path:
        raise AppError(404, "cover_not_found")
    path = media.resolve(track.cover_path)
    if not path.is_file():
        raise AppError(404, "cover_missing")
    return FileResponse(path, media_type=media.guess_media_type(path))
