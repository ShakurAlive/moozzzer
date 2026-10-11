"""Admin endpoints (stage 3.2): manual file upload for testing / personal mp3s."""

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.core.deps import AdminUser, SessionDep
from app.services import upload
from app.services.tracks import TrackOut

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.post("/tracks/upload", status_code=status.HTTP_201_CREATED)
async def upload_track(
    admin: AdminUser,
    session: SessionDep,
    file: Annotated[UploadFile, File()],
) -> TrackOut:
    return await upload.upload_track(session, admin, file)
