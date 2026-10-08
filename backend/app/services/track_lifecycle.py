"""Track file lifecycle: the "orphaned_at" bookkeeping (kept in Python, not in DB triggers).

A track is referenced while a row exists in user_library or playlist_tracks. Every service that
adds or removes such rows must call these functions in the same transaction. To avoid a race
between "remove last reference" and "add a new reference", both paths lock the track row with
SELECT ... FOR UPDATE before checking references. Implemented in task 3.6.
"""

import uuid
from collections.abc import Collection
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession


async def on_track_referenced(session: AsyncSession, track_id: uuid.UUID) -> None:
    """Call after inserting a user_library/playlist_tracks row: clears tracks.orphaned_at."""
    raise NotImplementedError


async def on_references_removed(session: AsyncSession, track_ids: Collection[uuid.UUID]) -> None:
    """Call after deleting library/playlist rows (incl. playlist or user deletion, which cascade).

    Sets orphaned_at = now() for the given tracks that have no references left and are not
    already orphaned. Callers that delete via ON DELETE CASCADE must collect track_ids first.
    """
    raise NotImplementedError


async def reconcile_orphans(session: AsyncSession) -> int:
    """Safety net for the nightly job: mark every unreferenced, non-orphaned track as orphaned
    and clear orphaned_at on referenced ones. Returns the number of rows changed."""
    raise NotImplementedError


async def collect_garbage(session: AsyncSession, older_than: datetime) -> list[uuid.UUID]:
    """Delete tracks orphaned before `older_than` (still unreferenced, re-checked under lock)
    and return their ids; the caller removes files from MEDIA_ROOT after commit."""
    raise NotImplementedError
