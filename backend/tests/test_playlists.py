"""Tests for playlists (stage 3.5): CRUD, add/remove, reorder."""

import uuid
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import create_access_token
from app.db.enums import TrackStatus, UserRole
from app.db.models import PlaylistTrack, Track, User
from app.db.session import SessionLocal, engine
from app.services import auth as auth_service
from app.services import playlists
from app.services.auth import NewUser
from app.services.playlists import PlaylistCreate, PlaylistUpdate

PASSWORD = "correct horse battery"


def unique() -> str:
    return uuid.uuid4().hex[:10]


def make_user(**kw: object) -> User:
    suffix = unique()
    defaults: dict[str, object] = {
        "email": f"u{suffix}@example.com",
        "username": f"u{suffix}",
        "password_hash": "x",
    }
    return User(**(defaults | kw))


def make_track(**kw: object) -> Track:
    defaults: dict[str, object] = {
        "title": "Song",
        "artist": "Artist",
        "source_provider": "upload",
        "source_id": uuid.uuid4().hex,
        "status": TrackStatus.READY,
        "file_path": "aa/song.mp3",
        "file_size": 10,
    }
    return Track(**(defaults | kw))


@pytest.fixture(autouse=True)
async def truncate() -> AsyncIterator[None]:
    yield
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE listen_events, playlist_tracks, playlists, user_library, "
                "tracks, refresh_tokens, invites, users CASCADE"
            )
        )


async def create_user(role: UserRole = UserRole.ADMIN) -> User:
    async with SessionLocal() as session:
        user = await auth_service.create_user(
            session,
            NewUser(email=f"{unique()}@example.com", username=f"u{unique()}", password=PASSWORD),
            role=role,
        )
        await session.commit()
    return user


async def create_ready_track() -> Track:
    async with SessionLocal() as session:
        track = make_track()
        session.add(track)
        await session.commit()
    return track


def bearer(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


# --- service layer ---


async def test_create_get_update_delete(db_session: AsyncSession) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    created = await playlists.create_playlist(db_session, user, PlaylistCreate(name="Mix"))
    assert created.track_count == 0

    detail = await playlists.get_playlist(db_session, user, created.id)
    assert detail.name == "Mix" and detail.tracks == []

    updated = await playlists.update_playlist(
        db_session, user, created.id, PlaylistUpdate(name="Road")
    )
    assert updated.name == "Road"

    await playlists.delete_playlist(db_session, user, created.id)
    with pytest.raises(AppError):
        await playlists.get_playlist(db_session, user, created.id)


async def test_add_remove_and_reorder(db_session: AsyncSession) -> None:
    user = make_user()
    t1, t2, t3 = make_track(), make_track(), make_track()
    db_session.add_all([user, t1, t2, t3])
    await db_session.flush()

    playlist = await playlists.create_playlist(db_session, user, PlaylistCreate(name="Mix"))
    for track in (t1, t2, t3):
        await playlists.add_track(db_session, user, playlist.id, track.id)

    detail = await playlists.get_playlist(db_session, user, playlist.id)
    assert [t.id for t in detail.tracks] == [t1.id, t2.id, t3.id]

    await playlists.reorder(db_session, user, playlist.id, [t3.id, t1.id, t2.id])
    detail = await playlists.get_playlist(db_session, user, playlist.id)
    assert [t.id for t in detail.tracks] == [t3.id, t1.id, t2.id]

    positions = sorted(
        (
            await db_session.scalars(
                select(PlaylistTrack.position).where(PlaylistTrack.playlist_id == playlist.id)
            )
        ).all()
    )
    assert positions == [Decimal(1), Decimal(2), Decimal(3)]

    await playlists.remove_track(db_session, user, playlist.id, t1.id)
    detail = await playlists.get_playlist(db_session, user, playlist.id)
    assert [t.id for t in detail.tracks] == [t3.id, t2.id]


async def test_reorder_requires_exact_track_set(db_session: AsyncSession) -> None:
    user = make_user()
    t1, t2 = make_track(), make_track()
    db_session.add_all([user, t1, t2])
    await db_session.flush()
    playlist = await playlists.create_playlist(db_session, user, PlaylistCreate(name="Mix"))
    await playlists.add_track(db_session, user, playlist.id, t1.id)

    with pytest.raises(AppError):
        await playlists.reorder(db_session, user, playlist.id, [t2.id])


# --- endpoints ---


async def test_playlist_endpoints(client: AsyncClient) -> None:
    user = await create_user()
    track = await create_ready_track()
    headers = bearer(user.id)

    create = await client.post("/api/v1/playlists", headers=headers, json={"name": "Mix"})
    assert create.status_code == 201
    playlist_id = create.json()["id"]

    add = await client.put(f"/api/v1/playlists/{playlist_id}/tracks/{track.id}", headers=headers)
    assert add.status_code == 204

    detail = await client.get(f"/api/v1/playlists/{playlist_id}", headers=headers)
    assert detail.status_code == 200
    assert [t["id"] for t in detail.json()["tracks"]] == [str(track.id)]

    reorder = await client.put(
        f"/api/v1/playlists/{playlist_id}/tracks",
        headers=headers,
        json={"track_ids": [str(track.id)]},
    )
    assert reorder.status_code == 204

    remove = await client.delete(
        f"/api/v1/playlists/{playlist_id}/tracks/{track.id}", headers=headers
    )
    assert remove.status_code == 204


async def test_playlist_not_found_for_other_user(client: AsyncClient) -> None:
    owner = await create_user()
    other = await create_user()
    create = await client.post("/api/v1/playlists", headers=bearer(owner.id), json={"name": "Mix"})
    playlist_id = create.json()["id"]

    resp = await client.get(f"/api/v1/playlists/{playlist_id}", headers=bearer(other.id))
    assert resp.status_code == 404
