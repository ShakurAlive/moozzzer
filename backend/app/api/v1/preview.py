from typing import Annotated

from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse

from app.core.deps import CurrentUser
from app.services import preview as preview_service

router = APIRouter(prefix="/v1/preview", tags=["preview"])


@router.get("/{provider}/{source_id}")
async def preview(
    user: CurrentUser,
    provider: str,
    source_id: str,
    range_header: Annotated[str | None, Header(alias="Range")] = None,
) -> StreamingResponse:
    return await preview_service.build_response(provider, source_id, range_header)
