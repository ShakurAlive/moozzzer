"""Invite management for admins (stage 1.3): create / list / revoke."""

import uuid

from fastapi import APIRouter, status

from app.core.deps import AdminUser, SessionDep
from app.services import auth as auth_service
from app.services.auth import InviteCreated, InviteOut

router = APIRouter(prefix="/v1/invites", tags=["invites"])


@router.get("")
async def list_invites(_admin: AdminUser, session: SessionDep) -> list[InviteOut]:
    return await auth_service.list_invites(session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_invite(admin: AdminUser, session: SessionDep) -> InviteCreated:
    invite, code = await auth_service.create_invite(session, created_by=admin.id)
    await session.commit()
    return InviteCreated(id=invite.id, code=code, expires_at=invite.expires_at)


@router.delete("/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(_admin: AdminUser, session: SessionDep, invite_id: uuid.UUID) -> None:
    await auth_service.revoke_invite(session, invite_id)
