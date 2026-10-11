"""Track file lifecycle: the "orphaned_at" bookkeeping (kept in Python, not in DB triggers).

A track is referenced while a row exists in ``user_library`` or ``playlist_tracks``. Every
service that adds or removes such rows calls these functions in the same transaction. To
avoid a race between "remove last reference" and "add a new reference", both paths lock
the track row with ``SELECT ... FOR UPDATE`` before checking references. Implemented in
task 3.6.
"""

import uuid
from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, union, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PlaylistTrack, Track, UserLibrary


@dataclass(frozen=True, slots=True)
class GarbageFile:
    """A track row deleted by :func:`collect_garbage`, with its files to unlink."""

    track_id: uuid.UUID
    file_path: str | None
    cover_path: str | None


async def _has_references(session: AsyncSession, track_id: uuid.UUID) -> bool:
    library = await session.scalar(
        select(func.count()).select_from(UserLibrary).where(UserLibrary.track_id == track_id)
    )
    if library:
        return True
    playlist = await session.scalar(
        select(func.count()).select_from(PlaylistTrack).where(PlaylistTrack.track_id == track_id)
    )
    return bool(playlist)


async def on_track_referenced(session: AsyncSession, track_id: uuid.UUID) -> None:
    """Call after inserting a user_library/playlist_tracks row: clears tracks.orphaned_at."""
    track = await session.scalar(select(Track).where(Track.id == track_id).with_for_update())
    if track is not None and track.orphaned_at is not None:
        track.orphaned_at = None


async def on_references_removed(session: AsyncSession, track_ids: Collection[uuid.UUID]) -> None:
    """Call after deleting library/playlist rows (incl. playlist or user deletion, which cascade).

    Sets orphaned_at = now() for the given tracks that have no references left and are not
    already orphaned. Callers that delete via ON DELETE CASCADE must collect track_ids first.
    """
    now = datetime.now(UTC)
    for track_id in set(track_ids):
        track = await session.scalar(select(Track).where(Track.id == track_id).with_for_update())
        if track is None or track.orphaned_at is not None:
            continue
        if not await _has_references(session, track_id):
            track.orphaned_at = now


async def reconcile_orphans(session: AsyncSession) -> int:
    """Safety net for the nightly job: mark every unreferenced, non-orphaned track as orphaned
    and clear orphaned_at on referenced ones. Returns the number of rows changed."""
    referenced = union(select(UserLibrary.track_id), select(PlaylistTrack.track_id)).subquery()
    now = datetime.now(UTC)

    cleared = cast(
        CursorResult[Any],
        await session.execute(
            update(Track)
            .where(Track.id.in_(select(referenced.c.track_id)), Track.orphaned_at.is_not(None))
            .values(orphaned_at=None)
        ),
    )
    orphaned = cast(
        CursorResult[Any],
        await session.execute(
            update(Track)
            .where(Track.id.not_in(select(referenced.c.track_id)), Track.orphaned_at.is_(None))
            .values(orphaned_at=now)
        ),
    )
    return cleared.rowcount + orphaned.rowcount


async def collect_garbage(session: AsyncSession, older_than: datetime) -> list[GarbageFile]:
    """Delete tracks orphaned before ``older_than`` (still unreferenced, re-checked under lock)
    and return their files; the caller removes them from MEDIA_ROOT after commit."""
    rows = (
        await session.scalars(
            select(Track)
            .where(Track.orphaned_at.is_not(None), Track.orphaned_at < older_than)
            .with_for_update(skip_locked=True)
        )
    ).all()

    garbage: list[GarbageFile] = []
    for track in rows:
        if await _has_references(session, track.id):
            # Re-attached since it was orphaned (e.g. grace-period restore) — clear the marker.
            track.orphaned_at = None
            continue
        garbage.append(GarbageFile(track.id, track.file_path, track.cover_path))
        await session.delete(track)
    await session.flush()
    return garbage
