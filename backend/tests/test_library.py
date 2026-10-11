"""Tests for the user library (stage 3.4): service layer + endpoints."""

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.enums import TrackStatus, UserRole
from app.db.models import Track, User
from app.db.session import SessionLocal, engine
from app.services import auth as auth_service
from app.services import library
from app.services.auth import NewUser

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


async def test_add_list_remove_library(db_session: AsyncSession) -> None:
    user, track = make_user(), make_track()
    db_session.add_all([user, track])
    await db_session.flush()

    await library.add_to_library(db_session, user, track.id)
    items = await library.list_library(db_session, user)
    assert [t.id for t in items] == [track.id]
    assert items[0].media_url is not None

    await library.remove_from_library(db_session, user, track.id)
    assert await library.list_library(db_session, user) == []
    assert track.orphaned_at is not None


async def test_add_to_library_is_idempotent(db_session: AsyncSession) -> None:
    user, track = make_user(), make_track()
    db_session.add_all([user, track])
    await db_session.flush()

    await library.add_to_library(db_session, user, track.id)
    await library.add_to_library(db_session, user, track.id)

    assert len(await library.list_library(db_session, user)) == 1


# --- endpoints ---


async def test_library_endpoints(client: AsyncClient) -> None:
    user = await create_user()
    track = await create_ready_track()
    headers = bearer(user.id)

    assert (await client.put(f"/api/v1/library/{track.id}", headers=headers)).status_code == 204

    resp = await client.get("/api/v1/library", headers=headers)
    assert resp.status_code == 200
    assert [t["id"] for t in resp.json()] == [str(track.id)]

    assert (await client.delete(f"/api/v1/library/{track.id}", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/library", headers=headers)).json() == []


async def test_library_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/library")).status_code == 401


async def test_library_add_missing_track(client: AsyncClient) -> None:
    user = await create_user()
    resp = await client.put(f"/api/v1/library/{uuid.uuid4()}", headers=bearer(user.id))

    assert resp.status_code == 404
    assert resp.json() == {"detail": "track_not_found"}
