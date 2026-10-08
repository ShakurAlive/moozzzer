import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPkMixin
from app.db.enums import TrackStatus, str_enum


class Track(UUIDPkMixin, TimestampMixin, Base):
    """A stored audio file, shared by all users (one file per source track)."""

    __tablename__ = "tracks"
    __table_args__ = (
        UniqueConstraint("source_provider", "source_id"),
        CheckConstraint(
            "status <> 'ready' OR (file_path IS NOT NULL AND file_size IS NOT NULL)",
            name="ready_has_file",
        ),
        CheckConstraint("duration_ms IS NULL OR duration_ms > 0", name="duration_positive"),
        CheckConstraint("file_size IS NULL OR file_size >= 0", name="file_size_non_negative"),
        CheckConstraint("bitrate_kbps IS NULL OR bitrate_kbps > 0", name="bitrate_positive"),
        CheckConstraint("isrc ~ '^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$'", name="isrc_format"),
        Index(
            "ix_tracks_orphaned_at",
            "orphaned_at",
            postgresql_where=text("orphaned_at IS NOT NULL"),
        ),
    )

    title: Mapped[str] = mapped_column(String(512))
    artist: Mapped[str] = mapped_column(String(512))
    album: Mapped[str | None] = mapped_column(String(512))
    duration_ms: Mapped[int | None]
    # Not unique: provider ISRC data is unreliable; dedup by ISRC happens in the service layer.
    isrc: Mapped[str | None] = mapped_column(String(12), index=True)
    explicit: Mapped[bool] = mapped_column(default=False, server_default=false())

    # "upload" for files added manually; otherwise a provider key from app/providers.
    source_provider: Mapped[str] = mapped_column(String(32))
    source_id: Mapped[str] = mapped_column(String(255))

    # Paths are relative to MEDIA_ROOT and never exposed to clients.
    file_path: Mapped[str | None] = mapped_column(String(1024))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    codec: Mapped[str | None] = mapped_column(String(16))
    bitrate_kbps: Mapped[int | None]
    cover_path: Mapped[str | None] = mapped_column(String(1024))

    status: Mapped[TrackStatus] = mapped_column(
        str_enum(TrackStatus, "track_status"),
        default=TrackStatus.PENDING,
        server_default=TrackStatus.PENDING,
    )
    error: Mapped[str | None] = mapped_column(Text)
    # Set by app.services.track_lifecycle when the last reference disappears; GC deletes later.
    orphaned_at: Mapped[datetime | None]


class UserLibrary(Base):
    __tablename__ = "user_library"
    __table_args__ = (Index("ix_user_library_user_id_added_at", "user_id", "added_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # RESTRICT: a track row may only disappear via GC once nothing references it.
    track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracks.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())
