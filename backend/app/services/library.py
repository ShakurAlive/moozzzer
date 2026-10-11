"""User library (stage 3.4): list, add (like), remove (unlike).

A track is "liked" exactly when it has a row in ``user_library``. Adding and
removing references goes through ``track_lifecycle`` so orphaned bookkeeping
stays correct (and, in the remove path, re-checks references under a row lock).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.models import Track, User, UserLibrary
from app.services import track_lifecycle, tracks
from app.services.tracks import TrackOut


async def list_library(session: AsyncSession, user: User) -> list[TrackOut]:
    rows = await session.scalars(
        select(Track)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .order_by(UserLibrary.added_at.desc())
    )
    return [tracks.to_dto(track) for track in rows.all()]


async def add_to_library(session: AsyncSession, user: User, track_id: uuid.UUID) -> None:
    # Lock the track row first so a concurrent "remove last reference" cannot
    # interleave between our insert and the orphaned_at update.
    track = await session.scalar(select(Track).where(Track.id == track_id).with_for_update())
    if track is None:
        raise AppError(404, "track_not_found")

    existing = await session.get(UserLibrary, (user.id, track_id))
    if existing is None:
        session.add(UserLibrary(user_id=user.id, track_id=track_id))
    await track_lifecycle.on_track_referenced(session, track_id)
    await session.commit()


async def remove_from_library(session: AsyncSession, user: User, track_id: uuid.UUID) -> None:
    row = await session.get(UserLibrary, (user.id, track_id))
    if row is not None:
        await session.delete(row)
    await track_lifecycle.on_references_removed(session, [track_id])
    await session.commit()
