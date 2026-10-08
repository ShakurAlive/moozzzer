import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPkMixin
from app.db.enums import UserRole, str_enum


class User(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint(
            "password_hash IS NOT NULL OR google_sub IS NOT NULL", name="has_credentials"
        ),
    )

    # Stored normalized (lower-case); the service layer lower-cases before insert/lookup.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    username: Mapped[str] = mapped_column(String(32))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    role: Mapped[UserRole] = mapped_column(
        str_enum(UserRole, "user_role"), default=UserRole.MEMBER, server_default=UserRole.MEMBER
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())


Index("uq_users_username_lower", func.lower(User.username), unique=True)


class Invite(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "invites"
    __table_args__ = (
        CheckConstraint("used_by IS NULL OR used_at IS NOT NULL", name="used_at_set"),
    )

    # sha256 hex of the code; the plain code is shown to the admin only once.
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    used_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True
    )
    used_at: Mapped[datetime | None]
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]


class RefreshToken(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # sha256 hex of the token; the raw token never touches the DB.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # All rotations of one login share a family; reuse of a revoked token revokes the family.
    family_id: Mapped[uuid.UUID] = mapped_column(index=True)
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    user_agent: Mapped[str | None] = mapped_column(String(512))
