import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ListenContext, TrackStatus, UserRole
from app.db.models import (
    Invite,
    ListenEvent,
    Playlist,
    PlaylistTrack,
    RefreshToken,
    Track,
    User,
    UserLibrary,
)


def make_user(**kw: object) -> User:
    suffix = uuid.uuid4().hex[:8]
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
    }
    return Track(**(defaults | kw))


async def test_one_row_per_table(db_session: AsyncSession) -> None:
    now = datetime.now(UTC)
    user = make_user()
    track = make_track(isrc="USRC17607839", duration_ms=180_000)
    db_session.add_all([user, track])
    await db_session.flush()

    playlist = Playlist(user_id=user.id, name="Road")
    db_session.add_all(
        [
            Invite(code_hash="a" * 64, created_by=user.id, expires_at=now + timedelta(days=7)),
            RefreshToken(
                user_id=user.id,
                token_hash="b" * 64,
                family_id=uuid.uuid4(),
                expires_at=now + timedelta(days=30),
            ),
            UserLibrary(user_id=user.id, track_id=track.id),
            playlist,
        ]
    )
    await db_session.flush()
    db_session.add_all(
        [
            PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=Decimal(1)),
            ListenEvent(
                user_id=user.id, track_id=track.id, started_at=now, context=ListenContext.LIBRARY
            ),
        ]
    )
    await db_session.flush()

    for model in (User, Invite, RefreshToken, Track, UserLibrary, Playlist, PlaylistTrack):
        assert await db_session.scalar(select(func.count()).select_from(model)) == 1
    event = await db_session.scalar(select(ListenEvent))
    assert event is not None and event.id > 0 and event.played_ms == 0

    await db_session.refresh(user)
    await db_session.refresh(track)
    assert user.role is UserRole.MEMBER and user.is_active
    assert user.created_at.tzinfo is not None
    assert track.status is TrackStatus.PENDING and track.orphaned_at is None


async def test_username_unique_case_insensitive(db_session: AsyncSession) -> None:
    db_session.add_all([make_user(username="Mom"), make_user(username="mom")])
    with pytest.raises(IntegrityError, match="uq_users_username_lower"):
        await db_session.flush()


async def test_user_requires_credentials(db_session: AsyncSession) -> None:
    db_session.add(make_user(password_hash=None))
    with pytest.raises(IntegrityError, match="ck_users_has_credentials"):
        await db_session.flush()


async def test_ready_track_requires_file(db_session: AsyncSession) -> None:
    db_session.add(make_track(status=TrackStatus.READY))
    with pytest.raises(IntegrityError, match="ck_tracks_ready_has_file"):
        await db_session.flush()


async def test_track_in_library_cannot_be_deleted(db_session: AsyncSession) -> None:
    user, track = make_user(), make_track()
    db_session.add_all([user, track])
    await db_session.flush()
    db_session.add(UserLibrary(user_id=user.id, track_id=track.id))
    await db_session.flush()

    await db_session.delete(track)
    with pytest.raises(IntegrityError, match="fk_user_library_track_id_tracks"):
        await db_session.flush()


async def test_playlist_insert_between_without_renumbering(db_session: AsyncSession) -> None:
    user = make_user()
    tracks = [make_track(title=t) for t in ("a", "b", "c")]
    db_session.add_all([user, *tracks])
    await db_session.flush()
    playlist = Playlist(user_id=user.id, name="Mix")
    db_session.add(playlist)
    await db_session.flush()

    a, b, c = tracks
    db_session.add_all(
        [
            PlaylistTrack(playlist_id=playlist.id, track_id=a.id, position=Decimal(1)),
            PlaylistTrack(playlist_id=playlist.id, track_id=c.id, position=Decimal(2)),
        ]
    )
    await db_session.flush()
    db_session.add(
        PlaylistTrack(playlist_id=playlist.id, track_id=b.id, position=(Decimal(1) + 2) / 2)
    )
    await db_session.flush()

    rows = await db_session.scalars(
        select(PlaylistTrack.track_id)
        .where(PlaylistTrack.playlist_id == playlist.id)
        .order_by(PlaylistTrack.position)
    )
    assert list(rows) == [a.id, b.id, c.id]


async def test_user_delete_cascades_but_keeps_tracks(db_session: AsyncSession) -> None:
    user, track = make_user(), make_track()
    db_session.add_all([user, track])
    await db_session.flush()
    db_session.add(UserLibrary(user_id=user.id, track_id=track.id))
    await db_session.flush()

    await db_session.delete(user)
    await db_session.flush()

    assert await db_session.scalar(select(func.count()).select_from(UserLibrary)) == 0
    assert await db_session.get(Track, track.id) is not None
