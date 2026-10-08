import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select, text

from app import cli
from app.core.config import get_settings
from app.core.deps import require_admin
from app.core.errors import AppError
from app.core.security import sha256_hex
from app.db.enums import UserRole
from app.db.models import Invite, RefreshToken, User
from app.db.session import SessionLocal, engine
from app.services import auth as auth_service
from app.services.auth import NewUser

PASSWORD = "correct horse battery"
MOBILE = {"X-Client": "mobile"}


@pytest.fixture(autouse=True)
async def truncate_auth_tables() -> AsyncIterator[None]:
    """These tests commit through the app's own sessions; leave the DB empty for other modules."""
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE users, invites, refresh_tokens CASCADE"))


def unique() -> str:
    return uuid.uuid4().hex[:10]


async def make_invite(**overrides: Any) -> str:
    async with SessionLocal() as session:
        invite, code = await auth_service.create_invite(session)
        for key, value in overrides.items():
            setattr(invite, key, value)
        await session.commit()
    return code


async def make_user(*, is_active: bool = True, role: UserRole = UserRole.MEMBER) -> User:
    suffix = unique()
    async with SessionLocal() as session:
        user = await auth_service.create_user(
            session,
            NewUser(email=f"{suffix}@example.com", username=f"u{suffix}", password=PASSWORD),
            role=role,
        )
        user.is_active = is_active
        await session.commit()
    return user


def register_body(code: str, **overrides: str) -> dict[str, str]:
    suffix = unique()
    body = {
        "invite_code": code,
        "email": f"New.{suffix}@Example.com",
        "username": f"new_{suffix}",
        "password": PASSWORD,
    }
    return body | overrides


async def login(client: AsyncClient, user: User, *, mobile: bool = False) -> Response:
    return await client.post(
        "/api/v1/auth/login",
        json={"email_or_username": user.email, "password": PASSWORD},
        headers=MOBILE if mobile else None,
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def refresh_mobile(client: AsyncClient, token: str) -> Response:
    return await client.post("/api/v1/auth/refresh", json={"refresh_token": token}, headers=MOBILE)


# --- register ---


async def test_register_web_sets_cookie_and_marks_invite_used(client: AsyncClient) -> None:
    code = await make_invite()
    body = register_body(code)

    resp = await client.post("/api/v1/auth/register", json=body)

    assert resp.status_code == 201
    data = resp.json()
    assert data["token_type"] == "bearer" and data["expires_in"] == 900
    assert data["refresh_token"] is None
    cookie = resp.headers["set-cookie"].lower()
    for attr in ("httponly", "secure", "samesite=strict", "path=/api/v1/auth"):
        assert attr in cookie

    me = await client.get("/api/v1/auth/me", headers=bearer(data["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == body["email"].lower()
    assert me.json()["role"] == "member"

    async with SessionLocal() as session:
        invite = await session.scalar(select(Invite).where(Invite.code_hash == sha256_hex(code)))
    assert invite is not None and invite.used_at is not None
    assert str(invite.used_by) == me.json()["id"]


async def test_register_mobile_returns_refresh_in_body(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register", json=register_body(await make_invite()), headers=MOBILE
    )

    assert resp.status_code == 201
    assert resp.json()["refresh_token"]
    assert "set-cookie" not in resp.headers


@pytest.mark.parametrize(
    "overrides",
    [
        {"used_at": datetime.now(UTC)},
        {"revoked_at": datetime.now(UTC)},
        {"expires_at": datetime.now(UTC) - timedelta(seconds=1)},
    ],
    ids=["used", "revoked", "expired"],
)
async def test_register_rejects_invalid_invite(
    client: AsyncClient, overrides: dict[str, Any]
) -> None:
    code = await make_invite(**overrides)

    resp = await client.post("/api/v1/auth/register", json=register_body(code))

    assert resp.status_code == 400
    assert resp.json() == {"detail": "invite_invalid"}


async def test_register_rejects_unknown_invite(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/register", json=register_body("nope"))

    assert resp.status_code == 400


async def test_invite_can_be_used_once(client: AsyncClient) -> None:
    code = await make_invite()

    first = await client.post("/api/v1/auth/register", json=register_body(code))
    second = await client.post("/api/v1/auth/register", json=register_body(code))

    assert (first.status_code, second.status_code) == (201, 400)


async def test_concurrent_registration_with_same_invite(client: AsyncClient) -> None:
    code = await make_invite()

    responses = await asyncio.gather(
        *(client.post("/api/v1/auth/register", json=register_body(code)) for _ in range(3))
    )

    assert sorted(r.status_code for r in responses) == [201, 400, 400]


async def test_register_duplicate_email_keeps_invite_unused(client: AsyncClient) -> None:
    existing = await make_user()
    code = await make_invite()

    dup = await client.post(
        "/api/v1/auth/register", json=register_body(code, email=existing.email.upper())
    )
    ok = await client.post("/api/v1/auth/register", json=register_body(code))

    assert dup.status_code == 409 and dup.json() == {"detail": "email_taken"}
    assert ok.status_code == 201


async def test_register_duplicate_username_case_insensitive(client: AsyncClient) -> None:
    existing = await make_user()

    resp = await client.post(
        "/api/v1/auth/register",
        json=register_body(await make_invite(), username=existing.username.upper()),
    )

    assert resp.status_code == 409 and resp.json() == {"detail": "username_taken"}


@pytest.mark.parametrize(
    "overrides",
    [{"password": "short7!"}, {"email": "not-an-email"}, {"username": "bad name"}],
    ids=["short-password", "bad-email", "bad-username"],
)
async def test_register_validates_input(client: AsyncClient, overrides: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/auth/register", json=register_body(await make_invite(), **overrides)
    )

    assert resp.status_code == 422


# --- login ---


async def test_login_by_email_or_username(client: AsyncClient) -> None:
    user = await make_user()

    for ident in (user.email.upper(), user.username.upper()):
        resp = await client.post(
            "/api/v1/auth/login", json={"email_or_username": ident, "password": PASSWORD}
        )
        assert resp.status_code == 200
        me = await client.get("/api/v1/auth/me", headers=bearer(resp.json()["access_token"]))
        assert me.json()["id"] == str(user.id)


async def test_login_same_error_for_wrong_password_and_unknown_user(client: AsyncClient) -> None:
    user = await make_user()

    wrong = await client.post(
        "/api/v1/auth/login", json={"email_or_username": user.email, "password": "x" * 10}
    )
    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email_or_username": f"{unique()}@example.com", "password": PASSWORD},
    )

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "invalid_credentials"}


async def test_login_inactive_user(client: AsyncClient) -> None:
    user = await make_user(is_active=False)

    resp = await login(client, user)

    assert resp.status_code == 403 and resp.json() == {"detail": "account_disabled"}


async def test_login_rate_limited(client: AsyncClient) -> None:
    user = await make_user()
    bad = {"email_or_username": user.email, "password": "wrong-password"}

    statuses = [(await client.post("/api/v1/auth/login", json=bad)).status_code for _ in range(5)]
    blocked = await login(client, user)

    assert statuses == [401] * 5
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


async def test_register_rate_limited_per_ip(client: AsyncClient) -> None:
    limit = get_settings().auth_rate_limit_ip_per_minute
    for _ in range(limit):
        resp = await client.post("/api/v1/auth/register", json=register_body("nope"))
        assert resp.status_code == 400

    resp = await client.post("/api/v1/auth/register", json=register_body("nope"))

    assert resp.status_code == 429


# --- me / deps ---


async def test_me_rejects_missing_invalid_and_expired_tokens(client: AsyncClient) -> None:
    user = await make_user()
    past = datetime.now(UTC) - timedelta(hours=1)
    expired = jwt.encode(
        {"sub": str(user.id), "type": "access", "iat": past, "exp": past + timedelta(minutes=15)},
        get_settings().jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    forged = jwt.encode(
        {"sub": str(user.id), "type": "access", "iat": datetime.now(UTC), "exp": 9999999999},
        "x" * 32,
        algorithm="HS256",
    )

    missing = await client.get("/api/v1/auth/me")
    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    for token in ("garbage", expired, forged):
        resp = await client.get("/api/v1/auth/me", headers=bearer(token))
        assert resp.status_code == 401, token


async def test_me_rejects_deactivated_user_with_valid_token(client: AsyncClient) -> None:
    user = await make_user()
    token = (await login(client, user)).json()["access_token"]
    async with SessionLocal() as session:
        db_user = await session.get(User, user.id)
        assert db_user is not None
        db_user.is_active = False
        await session.commit()

    resp = await client.get("/api/v1/auth/me", headers=bearer(token))

    assert resp.status_code == 401


async def test_require_admin() -> None:
    admin = await make_user(role=UserRole.ADMIN)
    member = await make_user()

    assert await require_admin(admin) is admin
    with pytest.raises(AppError) as exc:
        await require_admin(member)
    assert exc.value.status_code == 403


# --- refresh / logout ---


async def test_refresh_web_rotates_cookie(client: AsyncClient) -> None:
    user = await make_user()
    first = (await login(client, user)).cookies["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh")

    assert resp.status_code == 200
    assert resp.json()["access_token"]
    second = resp.cookies["refresh_token"]
    assert second and second != first

    async with SessionLocal() as session:
        old = await session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(first))
        )
        new = await session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(second))
        )
    assert old is not None and old.revoked_at is not None
    assert new is not None and new.revoked_at is None and new.family_id == old.family_id


async def test_refresh_mobile_and_reuse_revokes_family(client: AsyncClient) -> None:
    user = await make_user()
    r1 = (await login(client, user, mobile=True)).json()["refresh_token"]

    rotated = await refresh_mobile(client, r1)
    assert rotated.status_code == 200
    r2 = rotated.json()["refresh_token"]

    reuse = await refresh_mobile(client, r1)
    assert reuse.status_code == 401 and reuse.json() == {"detail": "invalid_refresh_token"}
    # The legitimate successor is revoked too: the family is compromised.
    assert (await refresh_mobile(client, r2)).status_code == 401


async def test_refresh_other_family_unaffected_by_reuse(client: AsyncClient) -> None:
    user = await make_user()
    a1 = (await login(client, user, mobile=True)).json()["refresh_token"]
    b1 = (await login(client, user, mobile=True)).json()["refresh_token"]

    await refresh_mobile(client, a1)
    await refresh_mobile(client, a1)

    assert (await refresh_mobile(client, b1)).status_code == 200


async def test_refresh_rejects_missing_unknown_and_expired(client: AsyncClient) -> None:
    user = await make_user()
    token = (await login(client, user, mobile=True)).json()["refresh_token"]
    async with SessionLocal() as session:
        row = await session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(token))
        )
        assert row is not None
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()

    assert (await client.post("/api/v1/auth/refresh")).status_code == 401
    assert (await refresh_mobile(client, "unknown")).status_code == 401
    assert (await refresh_mobile(client, token)).status_code == 401


async def test_refresh_rejects_deactivated_user(client: AsyncClient) -> None:
    user = await make_user()
    token = (await login(client, user, mobile=True)).json()["refresh_token"]
    async with SessionLocal() as session:
        db_user = await session.get(User, user.id)
        assert db_user is not None
        db_user.is_active = False
        await session.commit()

    assert (await refresh_mobile(client, token)).status_code == 401


async def test_logout_web_clears_cookie_and_revokes(client: AsyncClient) -> None:
    user = await make_user()
    token = (await login(client, user)).cookies["refresh_token"]

    resp = await client.post("/api/v1/auth/logout")

    assert resp.status_code == 204
    assert 'refresh_token=""' in resp.headers["set-cookie"]
    assert (await refresh_mobile(client, token)).status_code == 401


async def test_logout_mobile_is_idempotent(client: AsyncClient) -> None:
    user = await make_user()
    token = (await login(client, user, mobile=True)).json()["refresh_token"]

    for _ in range(2):
        resp = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": token}, headers=MOBILE
        )
        assert resp.status_code == 204
    assert (await refresh_mobile(client, token)).status_code == 401


# --- CLI ---


async def test_cli_create_admin_and_invite(client: AsyncClient) -> None:
    suffix = unique()
    await cli.create_admin(
        NewUser(email=f"Admin.{suffix}@example.com", username=f"a{suffix}", password=PASSWORD)
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email_or_username": f"a{suffix}", "password": PASSWORD},
    )
    me = await client.get("/api/v1/auth/me", headers=bearer(resp.json()["access_token"]))
    assert me.json()["role"] == "admin"
    assert me.json()["email"] == f"admin.{suffix}@example.com"

    code = await cli.create_invite(days=1)
    reg = await client.post("/api/v1/auth/register", json=register_body(code))
    assert reg.status_code == 201


def test_cli_prompt_rejects_mismatch_and_short_password(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = iter(["password-1", "password-2", "short", "short"])
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: next(answers))

    with pytest.raises(SystemExit, match="do not match"):
        cli._prompt_new_admin("a@example.com", "admin")
    with pytest.raises(SystemExit, match="password"):
        cli._prompt_new_admin("a@example.com", "admin")
