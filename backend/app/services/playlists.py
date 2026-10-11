"""Playlists (stage 3.5): CRUD, add/remove tracks, reorder.

Ordering uses the fractional ``position NUMERIC`` from ADR 0001: appending uses
``max + 1`` (never grows a fraction), and a full reorder renumbers ``1..n`` in
one deferred-constraint update — so the unique ``(playlist_id, position)`` is
never violated mid-transaction.
"""

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.models import Playlist, PlaylistTrack, Track, User
from app.services import track_lifecycle, tracks
from app.services.tracks import TrackOut

# Deferred to allow a full 1..n renumber as one UPDATE (see ADR 0001).
_POSITION_CONSTRAINT = "uq_playlist_tracks_playlist_id_position"


class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class PlaylistUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ReorderRequest(BaseModel):
    track_ids: list[uuid.UUID]


class PlaylistOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    cover_url: str | None
    track_count: int


class PlaylistDetail(PlaylistOut):
    tracks: list[TrackOut]


def _out(playlist: Playlist, track_count: int) -> PlaylistOut:
    return PlaylistOut(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        cover_url=None,
        track_count=track_count,
    )


async def _get_owned(session: AsyncSession, user: User, playlist_id: uuid.UUID) -> Playlist:
    playlist = await session.get(Playlist, playlist_id)
    if playlist is None or playlist.user_id != user.id:
        raise AppError(404, "playlist_not_found")
    return playlist


async def _track_count(session: AsyncSession, playlist_id: uuid.UUID) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist_id)
    )
    return int(count or 0)


async def list_playlists(session: AsyncSession, user: User) -> list[PlaylistOut]:
    rows = await session.execute(
        select(Playlist, func.count(PlaylistTrack.track_id))
        .outerjoin(PlaylistTrack, PlaylistTrack.playlist_id == Playlist.id)
        .where(Playlist.user_id == user.id)
        .group_by(Playlist.id)
        .order_by(Playlist.created_at.desc())
    )
    return [_out(playlist, int(count)) for playlist, count in rows.all()]


async def create_playlist(session: AsyncSession, user: User, data: PlaylistCreate) -> PlaylistOut:
    playlist = Playlist(user_id=user.id, name=data.name.strip(), description=data.description)
    session.add(playlist)
    await session.flush()
    await session.commit()
    return _out(playlist, 0)


async def get_playlist(session: AsyncSession, user: User, playlist_id: uuid.UUID) -> PlaylistDetail:
    playlist = await _get_owned(session, user, playlist_id)
    rows = await session.scalars(
        select(Track)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .order_by(PlaylistTrack.position)
    )
    track_list = [tracks.to_dto(track) for track in rows.all()]
    return PlaylistDetail(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        cover_url=None,
        track_count=len(track_list),
        tracks=track_list,
    )


async def update_playlist(
    session: AsyncSession, user: User, playlist_id: uuid.UUID, data: PlaylistUpdate
) -> PlaylistOut:
    playlist = await _get_owned(session, user, playlist_id)
    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise AppError(422, "playlist_name_blank")
        playlist.name = name
    if data.description is not None:
        playlist.description = data.description.strip() or None
    await session.commit()
    return _out(playlist, await _track_count(session, playlist_id))


async def delete_playlist(session: AsyncSession, user: User, playlist_id: uuid.UUID) -> None:
    playlist = await _get_owned(session, user, playlist_id)
    # Collect track ids before the cascade so orphaned bookkeeping can run.
    track_ids = list(
        await session.scalars(
            select(PlaylistTrack.track_id).where(PlaylistTrack.playlist_id == playlist_id)
        )
    )
    await session.delete(playlist)
    await session.flush()
    await track_lifecycle.on_references_removed(session, track_ids)
    await session.commit()


async def add_track(
    session: AsyncSession, user: User, playlist_id: uuid.UUID, track_id: uuid.UUID
) -> None:
    await _get_owned(session, user, playlist_id)
    track = await session.scalar(select(Track).where(Track.id == track_id).with_for_update())
    if track is None:
        raise AppError(404, "track_not_found")

    existing = await session.get(PlaylistTrack, (playlist_id, track_id))
    if existing is None:
        max_position = await session.scalar(
            select(func.max(PlaylistTrack.position)).where(PlaylistTrack.playlist_id == playlist_id)
        )
        position = (max_position or Decimal(0)) + 1
        session.add(PlaylistTrack(playlist_id=playlist_id, track_id=track_id, position=position))
    await track_lifecycle.on_track_referenced(session, track_id)
    await session.commit()


async def remove_track(
    session: AsyncSession, user: User, playlist_id: uuid.UUID, track_id: uuid.UUID
) -> None:
    await _get_owned(session, user, playlist_id)
    row = await session.get(PlaylistTrack, (playlist_id, track_id))
    if row is not None:
        await session.delete(row)
    await track_lifecycle.on_references_removed(session, [track_id])
    await session.commit()


async def reorder(
    session: AsyncSession, user: User, playlist_id: uuid.UUID, track_ids: list[uuid.UUID]
) -> None:
    await _get_owned(session, user, playlist_id)
    existing = set(
        await session.scalars(
            select(PlaylistTrack.track_id).where(PlaylistTrack.playlist_id == playlist_id)
        )
    )
    if set(track_ids) != existing:
        raise AppError(409, "playlist_tracks_mismatch")

    await session.execute(text(f"SET CONSTRAINTS {_POSITION_CONSTRAINT} DEFERRED"))
    for position, track_id in enumerate(track_ids, start=1):
        await session.execute(
            update(PlaylistTrack)
            .where(PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.track_id == track_id)
            .values(position=Decimal(position))
        )
    await session.commit()
