from enum import StrEnum

from sqlalchemy import Enum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class TrackStatus(StrEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    READY = "ready"
    FAILED = "failed"


class ListenContext(StrEnum):
    SEARCH = "search"
    LIBRARY = "library"
    PLAYLIST = "playlist"
    WAVE = "wave"


def str_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """VARCHAR + CHECK instead of a native PG enum: values change via a plain migration."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=16,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
    )
