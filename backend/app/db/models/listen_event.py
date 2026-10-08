import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Identity, Index, String, false
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ListenContext, str_enum


class ListenEvent(Base):
    __tablename__ = "listen_events"
    __table_args__ = (
        CheckConstraint("played_ms >= 0", name="played_ms_non_negative"),
        CheckConstraint("NOT (completed AND skipped)", name="completed_xor_skipped"),
        Index("ix_listen_events_user_id_started_at", "user_id", "started_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # NULL for search previews, or after the track was garbage-collected.
    track_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tracks.id", ondelete="SET NULL"), index=True
    )
    # "<provider>:<source_id>"; survives track deletion, identifies previews.
    provider_ref: Mapped[str | None] = mapped_column(String(300))
    started_at: Mapped[datetime]
    played_ms: Mapped[int] = mapped_column(default=0, server_default="0")
    completed: Mapped[bool] = mapped_column(default=False, server_default=false())
    skipped: Mapped[bool] = mapped_column(default=False, server_default=false())
    context: Mapped[ListenContext] = mapped_column(str_enum(ListenContext, "listen_context"))
