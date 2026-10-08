from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Domain error raised by services; rendered as `{"detail": code}` like HTTPException."""

    def __init__(self, status_code: int, code: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.headers = headers


async def app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return JSONResponse({"detail": exc.code}, status_code=exc.status_code, headers=exc.headers)
