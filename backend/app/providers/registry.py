"""Provider registry (stage 4.1).

Active providers are selected via env (``PROVIDERS_METADATA`` / ``PROVIDERS_AUDIO``).
Every provider runs under a common timeout and its failures are isolated, so one
broken provider never breaks the others. Search results are cached in Redis (TTL).

Stage 4.2 builds the search aggregator (dedup by ISRC, ranking, ``GET /search``)
on top of :func:`search`; here we only fan out and cache the raw results.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from functools import cache

from app.core.config import get_settings
from app.core.redis import redis_client
from app.core.security import sha256_hex
from app.providers import base
from app.providers.soundcloud import SoundCloudProvider
from app.providers.youtube_music import YouTubeMusicProvider

logger = logging.getLogger(__name__)

_METADATA: dict[str, Callable[[], base.MetadataProvider]] = {
    "youtube_music": YouTubeMusicProvider,
}
_AUDIO: dict[str, Callable[[], base.AudioProvider]] = {
    "youtube_music": YouTubeMusicProvider,
    "soundcloud": SoundCloudProvider,
}


@cache
def _metadata_instance(key: str) -> base.MetadataProvider | None:
    factory = _METADATA.get(key)
    return factory() if factory is not None else None


@cache
def _audio_instance(key: str) -> base.AudioProvider | None:
    factory = _AUDIO.get(key)
    return factory() if factory is not None else None


def _keys(raw: str) -> list[str]:
    return [key.strip() for key in raw.split(",") if key.strip()]


def enabled_metadata() -> list[base.MetadataProvider]:
    providers: list[base.MetadataProvider] = []
    for key in _keys(get_settings().providers_metadata):
        instance = _metadata_instance(key)
        if instance is None:
            logger.warning("Unknown metadata provider %r ignored", key)
        else:
            providers.append(instance)
    return providers


def enabled_audio() -> list[base.AudioProvider]:
    providers: list[base.AudioProvider] = []
    for key in _keys(get_settings().providers_audio):
        instance = _audio_instance(key)
        if instance is None:
            logger.warning("Unknown audio provider %r ignored", key)
        else:
            providers.append(instance)
    return providers


async def _search_safe(
    provider: base.MetadataProvider, query: str, limit: int
) -> list[base.TrackCandidate]:
    try:
        async with asyncio.timeout(get_settings().providers_timeout_seconds):
            return await provider.search(query, limit)
    except Exception:
        logger.warning("Metadata provider %r failed", provider.name, exc_info=True)
        return []


def _decode_candidates(raw: str) -> list[base.TrackCandidate]:
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    if not isinstance(data, list):
        return []
    return [base.TrackCandidate.model_validate(item) for item in data]


async def search(query: str, limit: int = 20) -> list[base.TrackCandidate]:
    """Fan out to every enabled metadata provider in parallel, cached in Redis."""
    settings = get_settings()
    key = f"providers:search:{sha256_hex(query.strip().lower())}:{limit}"

    cached = await redis_client.get(key)
    if cached is not None:
        return _decode_candidates(cached)

    providers = enabled_metadata()
    groups = await asyncio.gather(*(_search_safe(p, query, limit) for p in providers))
    candidates = [candidate for group in groups for candidate in group]

    payload = json.dumps([candidate.model_dump(mode="json") for candidate in candidates])
    await redis_client.set(key, payload, ex=settings.providers_cache_ttl_seconds)
    return candidates
