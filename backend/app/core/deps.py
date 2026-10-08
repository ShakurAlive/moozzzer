"""Shared FastAPI dependencies. Protected endpoints use `CurrentUser` / `AdminUser`:

@router.get("/things")
async def list_things(user: CurrentUser, session: SessionDep) -> list[Thing]: ...
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.enums import UserRole
from app.db.models import User
from app.db.session import SessionLocal

_bearer = HTTPBearer(auto_error=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Active user from `Authorization: Bearer <access JWT>`; loaded per request so that
    deactivation and role changes apply immediately."""
    user_id = decode_access_token(credentials.credentials) if credentials else None
    user = await session.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "not_authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role is not UserRole.ADMIN:
        raise AppError(status.HTTP_403_FORBIDDEN, "admin_required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
