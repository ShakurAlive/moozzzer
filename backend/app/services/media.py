"""Media storage and signed streaming URLs (stage 3.1).

Files live under ``MEDIA_ROOT/{aa}/{uuid}.{ext}`` where ``{aa}`` is the first two
hex digits of the track id (256 shards keep a single directory small). Paths
stored in the DB are always relative to ``MEDIA_ROOT`` and never exposed to
clients.

Clients cannot attach an ``Authorization`` header to ``<audio>``/``<img>``
requests, so streaming uses short-lived signed URLs instead:
``/api/v1/media/{track_id}?exp=<unix>&sig=<hmac>``. The signature is an
HMAC-SHA256 over ``"{track_id}:{exp}"`` and can be verified without a database
lookup, while the actual file path is looked up from the DB on each request.
"""

import hashlib
import hmac
import mimetypes
import os
import time
import uuid
from pathlib import Path

from app.core.config import get_settings


def _signing_secret() -> str:
    return get_settings().media_signing_secret.get_secret_value()


def _sign(payload: str) -> str:
    return hmac.new(_signing_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()


def shard_dir(track_id: uuid.UUID) -> str:
    """Two-hex-char directory shard (256 buckets)."""
    return track_id.hex[:2]


def audio_relpath(track_id: uuid.UUID, ext: str) -> str:
    return f"{shard_dir(track_id)}/{track_id}.{ext.lower()}"


def cover_relpath(track_id: uuid.UUID, ext: str) -> str:
    return f"{shard_dir(track_id)}/{track_id}.cover.{ext.lower()}"


def resolve(relpath: str) -> Path:
    """Absolute path for a DB-stored relative path, confined to MEDIA_ROOT."""
    root = Path(get_settings().media_root).resolve()
    path = (root / relpath).resolve()
    if not path.is_relative_to(root):
        raise ValueError("media path escapes MEDIA_ROOT")
    return path


def signed_query(track_id: uuid.UUID) -> str:
    exp = str(int(time.time()) + get_settings().media_url_ttl_seconds)
    return f"exp={exp}&sig={_sign(f'{track_id}:{exp}')}"


def media_url(track_id: uuid.UUID) -> str:
    return f"/api/v1/media/{track_id}?{signed_query(track_id)}"


def cover_url(track_id: uuid.UUID) -> str:
    return f"/api/v1/media/{track_id}/cover?{signed_query(track_id)}"


def verify(track_id: uuid.UUID, exp: str, sig: str) -> bool:
    """True if the signature matches and has not expired yet."""
    try:
        expires = int(exp)
    except ValueError:
        return False
    if expires < int(time.time()):
        return False
    return hmac.compare_digest(_sign(f"{track_id}:{exp}"), sig)


def guess_media_type(path: Path) -> str:
    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"


def write_atomic(relpath: str, data: bytes) -> Path:
    """Write ``data`` to ``MEDIA_ROOT/{relpath}`` atomically; returns the full path."""
    full = resolve(relpath)
    full.parent.mkdir(parents=True, exist_ok=True)
    tmp = full.with_name(f".{full.name}.{uuid.uuid4().hex}.part")
    tmp.write_bytes(data)
    os.replace(tmp, full)
    return full
