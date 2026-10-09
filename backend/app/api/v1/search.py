from fastapi import APIRouter, Query

from app.core.deps import CurrentUser
from app.providers import base
from app.services import search as search_service

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.get("")
async def search_tracks(
    user: CurrentUser,
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[base.TrackCandidate]:
    return await search_service.search_tracks(q, limit)
