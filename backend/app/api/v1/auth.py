from typing import Annotated

from fastapi import APIRouter, Cookie, Header, Request, Response, status

from app.core.config import get_settings
from app.core.deps import CurrentUser, SessionDep
from app.services import auth as auth_service
from app.services.auth import (
    IssuedTokens,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"

ClientHeader = Annotated[str | None, Header(alias="X-Client")]
RefreshCookie = Annotated[str | None, Cookie(alias=REFRESH_COOKIE)]
UserAgent = Annotated[str | None, Header(alias="User-Agent")]


def _is_mobile(x_client: str | None) -> bool:
    return x_client == "mobile"


def _client_ip(request: Request) -> str:
    # Behind Caddy, uvicorn --proxy-headers puts the real client address here.
    return request.client.host if request.client else "unknown"


def _token_response(
    tokens: IssuedTokens, response: Response, x_client: str | None
) -> TokenResponse:
    if _is_mobile(x_client):
        return TokenResponse(
            access_token=tokens.access_token,
            expires_in=tokens.expires_in,
            refresh_token=tokens.refresh_token,
        )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.refresh_token,
        max_age=get_settings().refresh_token_ttl_days * 86400,
        path=REFRESH_COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return TokenResponse(access_token=tokens.access_token, expires_in=tokens.expires_in)


def _presented_refresh_token(
    x_client: str | None, cookie: str | None, body: RefreshRequest | None
) -> str | None:
    if _is_mobile(x_client):
        return body.refresh_token if body else None
    return cookie


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    session: SessionDep,
    x_client: ClientHeader = None,
    user_agent: UserAgent = None,
) -> TokenResponse:
    tokens = await auth_service.register(
        session, data, ip=_client_ip(request), user_agent=user_agent
    )
    return _token_response(tokens, response, x_client)


@router.post("/login")
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
    x_client: ClientHeader = None,
    user_agent: UserAgent = None,
) -> TokenResponse:
    tokens = await auth_service.login(session, data, ip=_client_ip(request), user_agent=user_agent)
    return _token_response(tokens, response, x_client)


@router.post("/refresh")
async def refresh(
    response: Response,
    session: SessionDep,
    body: RefreshRequest | None = None,
    x_client: ClientHeader = None,
    refresh_cookie: RefreshCookie = None,
    user_agent: UserAgent = None,
) -> TokenResponse:
    raw = _presented_refresh_token(x_client, refresh_cookie, body)
    tokens = await auth_service.rotate_refresh_token(session, raw, user_agent=user_agent)
    return _token_response(tokens, response, x_client)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    session: SessionDep,
    body: RefreshRequest | None = None,
    x_client: ClientHeader = None,
    refresh_cookie: RefreshCookie = None,
) -> Response:
    await auth_service.revoke_refresh_token(
        session, _presented_refresh_token(x_client, refresh_cookie, body)
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, secure=True, httponly=True, samesite="strict"
    )
    return response


@router.get("/me")
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
