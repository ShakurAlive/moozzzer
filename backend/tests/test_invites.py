"""Tests for admin invite management (stage 1.3)."""

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.security import create_access_token
from app.db.enums import UserRole
from app.db.session import SessionLocal, engine
from app.services import auth as auth_service
from app.services.auth import NewUser

PASSWORD = "correct horse battery"


def unique() -> str:
    return uuid.uuid4().hex[:10]


@pytest.fixture(autouse=True)
async def truncate() -> AsyncIterator[None]:
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE invites, refresh_tokens, users CASCADE"))


async def create_user(role: UserRole = UserRole.ADMIN):
    async with SessionLocal() as session:
        user = await auth_service.create_user(
            session,
            NewUser(email=f"{unique()}@example.com", username=f"u{unique()}", password=PASSWORD),
            role=role,
        )
        await session.commit()
    return user


def bearer(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def test_create_list_revoke_invite(client: AsyncClient) -> None:
    admin = await create_user()
    headers = bearer(admin.id)

    created = await client.post("/api/v1/invites", headers=headers)
    assert created.status_code == 201
    invite_id = created.json()["id"]
    assert created.json()["code"]

    listed = await client.get("/api/v1/invites", headers=headers)
    assert listed.status_code == 200
    assert invite_id in {item["id"] for item in listed.json()}

    revoked = await client.delete(f"/api/v1/invites/{invite_id}", headers=headers)
    assert revoked.status_code == 204

    listed = await client.get("/api/v1/invites", headers=headers)
    invite = next(item for item in listed.json() if item["id"] == invite_id)
    assert invite["revoked_at"] is not None


async def test_invites_require_admin(client: AsyncClient) -> None:
    member = await create_user(role=UserRole.MEMBER)
    headers = bearer(member.id)

    assert (await client.get("/api/v1/invites", headers=headers)).status_code == 403
    assert (await client.post("/api/v1/invites", headers=headers)).status_code == 403
