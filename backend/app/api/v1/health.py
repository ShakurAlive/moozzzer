from fastapi import APIRouter, Response, status

from app.services.health import HealthReport, check_health

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    response_model=HealthReport,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthReport}},
)
async def health(response: Response) -> HealthReport:
    report = await check_health()
    if report.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report
