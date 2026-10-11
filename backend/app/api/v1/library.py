"""User library endpoints (stage 3.4)."""

import uuid

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, SessionDep
from app.services import library
from app.services.tracks import TrackOut

router = APIRouter(prefix="/v1/library", tags=["library"])


@router.get("")
async def list_library(user: CurrentUser, session: SessionDep) -> list[TrackOut]:
    return await library.list_library(session, user)


@router.put("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_library(user: CurrentUser, session: SessionDep, track_id: uuid.UUID) -> None:
    await library.add_to_library(session, user, track_id)


@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_library(user: CurrentUser, session: SessionDep, track_id: uuid.UUID) -> None:
    await library.remove_from_library(session, user, track_id)
