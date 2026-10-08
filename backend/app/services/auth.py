"""Auth: registration by invite, login, refresh-token rotation, logout, admin CLI helpers.

Refresh tokens are opaque 256-bit strings; only their sha256 is stored. Every login starts a
token family; each refresh revokes the presented token and issues a new one in the same family.
Presenting an already revoked token means theft (or replay) -> the whole family is revoked.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import rate_limit
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    hash_password,
    new_opaque_token,
    sha256_hex,
    verify_password,
)
from app.db.enums import UserRole
from app.db.models import Invite, RefreshToken, User

PASSWORD_MIN_LENGTH = 8
# Bounds argon2 work per request.
PASSWORD_MAX_LENGTH = 256
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"
INVITE_TTL = timedelta(days=7)


def _normalize_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


class NewUser(BaseModel):
    email: Annotated[
        str, BeforeValidator(_normalize_email), Field(max_length=320, pattern=EMAIL_PATTERN)
    ]
    username: str = Field(min_length=3, max_length=32, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class RegisterRequest(NewUser):
    invite_code: str = Field(min_length=1, max_length=128)


class LoginRequest(BaseModel):
    email_or_username: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class RefreshRequest(BaseModel):
    """Body for mobile clients (`X-Client: mobile`); web sends the httpOnly cookie instead."""

    refresh_token: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int
    # Only for mobile clients; web gets it as an httpOnly cookie.
    refresh_token: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    role: UserRole
    created_at: datetime


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


def _invalid_refresh() -> AppError:
    return AppError(HTTPStatus.UNAUTHORIZED, "invalid_refresh_token")


async def _limit(scope: str, ip: str, identity: str) -> None:
    settings = get_settings()
    await rate_limit.hit(f"{scope}:ip", ip, limit=settings.auth_rate_limit_ip_per_minute)
    await rate_limit.hit(scope, f"{ip}|{identity}", limit=settings.auth_rate_limit_per_minute)


def _issue_tokens(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    user_agent: str | None,
    family_id: uuid.UUID | None = None,
) -> IssuedTokens:
    """Adds a refresh-token row to the session; the caller commits."""
    settings = get_settings()
    raw = new_opaque_token()
    session.add(
        RefreshToken(
            user_id=user_id,
            token_hash=sha256_hex(raw),
            family_id=family_id or uuid.uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days),
            user_agent=user_agent[:512] if user_agent else None,
        )
    )
    return IssuedTokens(
        access_token=create_access_token(user_id),
        refresh_token=raw,
        expires_in=settings.access_token_ttl_seconds,
    )


async def create_user(
    session: AsyncSession, data: NewUser, *, role: UserRole = UserRole.MEMBER
) -> User:
    """Inserts (flushes, does not commit). On a duplicate the session is rolled back -> 409."""
    user = User(
        email=data.email,
        username=data.username,
        password_hash=await asyncio.to_thread(hash_password, data.password),
        role=role,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        message = str(exc.orig)
        if "uq_users_email" in message:
            raise AppError(HTTPStatus.CONFLICT, "email_taken") from None
        if "uq_users_username_lower" in message:
            raise AppError(HTTPStatus.CONFLICT, "username_taken") from None
        raise
    return user


async def create_invite(
    session: AsyncSession, *, created_by: uuid.UUID | None = None, ttl: timedelta = INVITE_TTL
) -> tuple[Invite, str]:
    """Returns the invite and its plain code (shown once, only the hash is stored)."""
    code = new_opaque_token(24)
    invite = Invite(
        code_hash=sha256_hex(code), created_by=created_by, expires_at=datetime.now(UTC) + ttl
    )
    session.add(invite)
    await session.flush()
    return invite, code


async def register(
    session: AsyncSession, data: RegisterRequest, *, ip: str, user_agent: str | None
) -> IssuedTokens:
    await _limit("register", ip, data.email)
    # Row lock: a concurrent registration with the same code waits here and then sees used_at.
    invite = await session.scalar(
        select(Invite).where(Invite.code_hash == sha256_hex(data.invite_code)).with_for_update()
    )
    now = datetime.now(UTC)
    if (
        invite is None
        or invite.used_at is not None
        or invite.revoked_at is not None
        or invite.expires_at <= now
    ):
        await session.rollback()
        raise AppError(HTTPStatus.BAD_REQUEST, "invite_invalid")

    user = await create_user(session, data)
    invite.used_by = user.id
    invite.used_at = now
    tokens = _issue_tokens(session, user.id, user_agent=user_agent)
    await session.commit()
    return tokens


async def login(
    session: AsyncSession, data: LoginRequest, *, ip: str, user_agent: str | None
) -> IssuedTokens:
    ident = data.email_or_username.strip().lower()
    await _limit("login", ip, ident)
    column = User.email if "@" in ident else func.lower(User.username)
    user = await session.scalar(select(User).where(column == ident))

    # Always runs argon2 (dummy hash for unknown users) -> same timing and error for both cases.
    password_ok = await asyncio.to_thread(
        verify_password, user.password_hash if user else None, data.password
    )
    if user is None or not password_ok:
        raise AppError(HTTPStatus.UNAUTHORIZED, "invalid_credentials")
    # Only revealed to someone who knows the password.
    if not user.is_active:
        raise AppError(HTTPStatus.FORBIDDEN, "account_disabled")

    tokens = _issue_tokens(session, user.id, user_agent=user_agent)
    await session.commit()
    return tokens


async def rotate_refresh_token(
    session: AsyncSession, raw_token: str | None, *, user_agent: str | None
) -> IssuedTokens:
    if not raw_token:
        raise _invalid_refresh()
    token = await session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == sha256_hex(raw_token))
        .with_for_update()
    )
    if token is None:
        raise _invalid_refresh()

    now = datetime.now(UTC)
    if token.revoked_at is not None:
        await _revoke_family(session, token.family_id, now)
        await session.commit()
        raise _invalid_refresh()
    if token.expires_at <= now:
        raise _invalid_refresh()

    user = await session.get(User, token.user_id)
    if user is None or not user.is_active:
        await _revoke_family(session, token.family_id, now)
        await session.commit()
        raise _invalid_refresh()

    token.revoked_at = now
    tokens = _issue_tokens(session, user.id, user_agent=user_agent, family_id=token.family_id)
    await session.commit()
    return tokens


async def revoke_refresh_token(session: AsyncSession, raw_token: str | None) -> None:
    """Idempotent logout: unknown or already revoked tokens are ignored."""
    if not raw_token:
        return
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == sha256_hex(raw_token), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )
    await session.commit()


async def _revoke_family(session: AsyncSession, family_id: uuid.UUID, now: datetime) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
