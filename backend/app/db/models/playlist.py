import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPkMixin


class Playlist(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "playlists"
    __table_args__ = (CheckConstraint("length(btrim(name)) > 0", name="name_not_blank"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    cover_path: Mapped[str | None] = mapped_column(String(1024))


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    __table_args__ = (
        # Deferrable so a full renumbering can run as one UPDATE (SET CONSTRAINTS ... DEFERRED).
        UniqueConstraint(
            "playlist_id",
            "position",
            deferrable=True,
            initially="IMMEDIATE",
        ),
    )

    playlist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracks.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    # Fractional ordering: insert between a and b with (a + b) / 2; append with max + 1.
    position: Mapped[Decimal] = mapped_column(Numeric)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())
