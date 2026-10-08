"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-08

Additive only (CREATE TABLE / CREATE INDEX on new tables) and runs in one transaction,
so a failure leaves the database untouched. See docs/adr/0001-db-schema.md.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_pk() -> sa.Column[object]:
    return sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False)


def _ts(name: str, *, nullable: bool = False, default_now: bool = True) -> sa.Column[object]:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.text("now()") if default_now else None,
        nullable=nullable,
    )


def upgrade() -> None:
    op.create_table(
        "users",
        _uuid_pk(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("username", sa.String(32), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("google_sub", sa.String(255), nullable=True),
        sa.Column("role", sa.String(16), server_default="member", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("google_sub", name=op.f("uq_users_google_sub")),
        sa.CheckConstraint("role IN ('admin', 'member')", name=op.f("ck_users_user_role")),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_email_lowercase")),
        sa.CheckConstraint(
            "password_hash IS NOT NULL OR google_sub IS NOT NULL",
            name=op.f("ck_users_has_credentials"),
        ),
    )
    op.create_index(
        "uq_users_username_lower", "users", [sa.literal_column("lower(username)")], unique=True
    )

    op.create_table(
        "invites",
        _uuid_pk(),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("used_by", sa.Uuid(), nullable=True),
        _ts("used_at", nullable=True, default_now=False),
        _ts("expires_at", default_now=False),
        _ts("revoked_at", nullable=True, default_now=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invites")),
        sa.UniqueConstraint("code_hash", name=op.f("uq_invites_code_hash")),
        sa.UniqueConstraint("used_by", name=op.f("uq_invites_used_by")),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_invites_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["used_by"], ["users.id"], name=op.f("fk_invites_used_by_users"), ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "used_by IS NULL OR used_at IS NOT NULL", name=op.f("ck_invites_used_at_set")
        ),
    )

    op.create_table(
        "refresh_tokens",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        _ts("expires_at", default_now=False),
        _ts("revoked_at", nullable=True, default_now=False),
        sa.Column("user_agent", sa.String(512), nullable=True),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_refresh_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])
    op.create_index(op.f("ix_refresh_tokens_family_id"), "refresh_tokens", ["family_id"])

    op.create_table(
        "tracks",
        _uuid_pk(),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("artist", sa.String(512), nullable=False),
        sa.Column("album", sa.String(512), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("isrc", sa.String(12), nullable=True),
        sa.Column("explicit", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_provider", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("codec", sa.String(16), nullable=True),
        sa.Column("bitrate_kbps", sa.Integer(), nullable=True),
        sa.Column("cover_path", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        _ts("orphaned_at", nullable=True, default_now=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tracks")),
        sa.UniqueConstraint(
            "source_provider", "source_id", name=op.f("uq_tracks_source_provider_source_id")
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'downloading', 'ready', 'failed')",
            name=op.f("ck_tracks_track_status"),
        ),
        sa.CheckConstraint(
            "status <> 'ready' OR (file_path IS NOT NULL AND file_size IS NOT NULL)",
            name=op.f("ck_tracks_ready_has_file"),
        ),
        sa.CheckConstraint(
            "duration_ms IS NULL OR duration_ms > 0", name=op.f("ck_tracks_duration_positive")
        ),
        sa.CheckConstraint(
            "file_size IS NULL OR file_size >= 0", name=op.f("ck_tracks_file_size_non_negative")
        ),
        sa.CheckConstraint(
            "bitrate_kbps IS NULL OR bitrate_kbps > 0", name=op.f("ck_tracks_bitrate_positive")
        ),
        sa.CheckConstraint(
            "isrc ~ '^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$'", name=op.f("ck_tracks_isrc_format")
        ),
    )
    op.create_index(op.f("ix_tracks_isrc"), "tracks", ["isrc"])
    op.create_index(
        "ix_tracks_orphaned_at",
        "tracks",
        ["orphaned_at"],
        postgresql_where=sa.text("orphaned_at IS NOT NULL"),
    )

    op.create_table(
        "user_library",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        _ts("added_at"),
        sa.PrimaryKeyConstraint("user_id", "track_id", name=op.f("pk_user_library")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_library_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_user_library_track_id_tracks"),
            ondelete="RESTRICT",
        ),
    )
    op.create_index(op.f("ix_user_library_track_id"), "user_library", ["track_id"])
    op.create_index("ix_user_library_user_id_added_at", "user_library", ["user_id", "added_at"])

    op.create_table(
        "playlists",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_path", sa.String(1024), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_playlists")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_playlists_user_id_users"), ondelete="CASCADE"
        ),
        sa.CheckConstraint("length(btrim(name)) > 0", name=op.f("ck_playlists_name_not_blank")),
    )
    op.create_index(op.f("ix_playlists_user_id"), "playlists", ["user_id"])

    op.create_table(
        "playlist_tracks",
        sa.Column("playlist_id", sa.Uuid(), nullable=False),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Numeric(), nullable=False),
        _ts("added_at"),
        sa.PrimaryKeyConstraint("playlist_id", "track_id", name=op.f("pk_playlist_tracks")),
        sa.UniqueConstraint(
            "playlist_id",
            "position",
            name=op.f("uq_playlist_tracks_playlist_id_position"),
            deferrable=True,
            initially="IMMEDIATE",
        ),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["playlists.id"],
            name=op.f("fk_playlist_tracks_playlist_id_playlists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_playlist_tracks_track_id_tracks"),
            ondelete="RESTRICT",
        ),
    )
    op.create_index(op.f("ix_playlist_tracks_track_id"), "playlist_tracks", ["track_id"])

    op.create_table(
        "listen_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("track_id", sa.Uuid(), nullable=True),
        sa.Column("provider_ref", sa.String(300), nullable=True),
        _ts("started_at", default_now=False),
        sa.Column("played_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("skipped", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("context", sa.String(16), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listen_events")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_listen_events_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_listen_events_track_id_tracks"),
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "context IN ('search', 'library', 'playlist', 'wave')",
            name=op.f("ck_listen_events_listen_context"),
        ),
        sa.CheckConstraint("played_ms >= 0", name=op.f("ck_listen_events_played_ms_non_negative")),
        sa.CheckConstraint(
            "NOT (completed AND skipped)", name=op.f("ck_listen_events_completed_xor_skipped")
        ),
    )
    op.create_index(op.f("ix_listen_events_track_id"), "listen_events", ["track_id"])
    op.create_index(
        "ix_listen_events_user_id_started_at", "listen_events", ["user_id", "started_at"]
    )


def downgrade() -> None:
    # Dev/test only: never run on prod (drops all data). Indexes go with their tables.
    for table in (
        "listen_events",
        "playlist_tracks",
        "playlists",
        "user_library",
        "tracks",
        "refresh_tokens",
        "invites",
        "users",
    ):
        op.drop_table(table)
