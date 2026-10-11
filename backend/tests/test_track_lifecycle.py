"""Tests for track orphan bookkeeping and GC (stage 3.6)."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import TrackStatus
from app.db.models import Playlist, PlaylistTrack, Track, User, UserLibrary
from app.services import track_lifecycle


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
        "status": TrackStatus.READY,
        "file_path": "aa/song.mp3",
        "file_size": 100,
    }
    return Track(**(defaults | kw))


async def test_on_track_referenced_clears_orphan(db_session: AsyncSession) -> None:
    track = make_track(orphaned_at=datetime.now(UTC))
    db_session.add(track)
    await db_session.flush()

    await track_lifecycle.on_track_referenced(db_session, track.id)
    await db_session.flush()

    assert track.orphaned_at is None


async def test_on_references_removed_marks_orphan_when_unreferenced(
    db_session: AsyncSession,
) -> None:
    user, track = make_user(), make_track()
    db_session.add_all([user, track])
    await db_session.flush()
    db_session.add(UserLibrary(user_id=user.id, track_id=track.id))
    await db_session.flush()

    await db_session.delete(await db_session.get(UserLibrary, (user.id, track.id)))
    await db_session.flush()
    await track_lifecycle.on_references_removed(db_session, [track.id])
    await db_session.flush()

    assert track.orphaned_at is not None


async def test_on_references_removed_keeps_referenced_track(db_session: AsyncSession) -> None:
    user, track = make_user(), make_track()
    db_session.add_all([user, track])
    await db_session.flush()
    db_session.add(UserLibrary(user_id=user.id, track_id=track.id))
    await db_session.flush()

    await track_lifecycle.on_references_removed(db_session, [track.id])
    await db_session.flush()

    assert track.orphaned_at is None


async def test_reconcile_orphans(db_session: AsyncSession) -> None:
    user = make_user()
    orphan = make_track()
    referenced = make_track()
    db_session.add_all([user, orphan, referenced])
    await db_session.flush()
    db_session.add(UserLibrary(user_id=user.id, track_id=referenced.id))
    await db_session.flush()

    changed = await track_lifecycle.reconcile_orphans(db_session)
    await db_session.flush()

    assert orphan.orphaned_at is not None
    assert referenced.orphaned_at is None
    assert changed == 1


async def test_collect_garbage(db_session: AsyncSession) -> None:
    user = make_user()
    dead = make_track(orphaned_at=datetime.now(UTC) - timedelta(days=8))
    recent = make_track(orphaned_at=datetime.now(UTC) - timedelta(days=1))
    keep = make_track(orphaned_at=datetime.now(UTC) - timedelta(days=8))
    db_session.add_all([user, dead, recent, keep])
    await db_session.flush()
    db_session.add(UserLibrary(user_id=user.id, track_id=keep.id))
    await db_session.flush()

    older_than = datetime.now(UTC) - timedelta(days=7)
    garbage = await track_lifecycle.collect_garbage(db_session, older_than)
    await db_session.flush()

    assert {g.track_id for g in garbage} == {dead.id}
    assert await db_session.get(Track, dead.id) is None
    assert await db_session.get(Track, recent.id) is not None
    assert await db_session.get(Track, keep.id) is not None
    assert keep.orphaned_at is None


async def test_delete_playlist_cascades_and_orphans(db_session: AsyncSession) -> None:
    user = make_user()
    track = make_track()
    db_session.add_all([user, track])
    await db_session.flush()
    playlist = Playlist(user_id=user.id, name="Mix")
    db_session.add(playlist)
    await db_session.flush()
    db_session.add(PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=Decimal(1)))
    await db_session.flush()

    await db_session.delete(playlist)
    await db_session.flush()
    await track_lifecycle.on_references_removed(db_session, [track.id])
    await db_session.flush()

    assert track.orphaned_at is not None
