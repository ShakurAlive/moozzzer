"""Playlist endpoints (stage 3.5)."""

import uuid

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, SessionDep
from app.services import playlists
from app.services.playlists import (
    PlaylistCreate,
    PlaylistDetail,
    PlaylistOut,
    PlaylistUpdate,
    ReorderRequest,
)

router = APIRouter(prefix="/v1/playlists", tags=["playlists"])


@router.get("")
async def list_playlists(user: CurrentUser, session: SessionDep) -> list[PlaylistOut]:
    return await playlists.list_playlists(session, user)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    user: CurrentUser, session: SessionDep, data: PlaylistCreate
) -> PlaylistOut:
    return await playlists.create_playlist(session, user, data)


@router.get("/{playlist_id}")
async def get_playlist(
    user: CurrentUser, session: SessionDep, playlist_id: uuid.UUID
) -> PlaylistDetail:
    return await playlists.get_playlist(session, user, playlist_id)


@router.patch("/{playlist_id}")
async def update_playlist(
    user: CurrentUser, session: SessionDep, playlist_id: uuid.UUID, data: PlaylistUpdate
) -> PlaylistOut:
    return await playlists.update_playlist(session, user, playlist_id, data)


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(user: CurrentUser, session: SessionDep, playlist_id: uuid.UUID) -> None:
    await playlists.delete_playlist(session, user, playlist_id)


@router.put("/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_track(
    user: CurrentUser, session: SessionDep, playlist_id: uuid.UUID, track_id: uuid.UUID
) -> None:
    await playlists.add_track(session, user, playlist_id, track_id)


@router.delete("/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_track(
    user: CurrentUser, session: SessionDep, playlist_id: uuid.UUID, track_id: uuid.UUID
) -> None:
    await playlists.remove_track(session, user, playlist_id, track_id)


@router.put("/{playlist_id}/tracks", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_tracks(
    user: CurrentUser, session: SessionDep, playlist_id: uuid.UUID, data: ReorderRequest
) -> None:
    await playlists.reorder(session, user, playlist_id, data.track_ids)
