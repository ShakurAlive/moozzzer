"""Preview streaming (stage 4.7).

Resolve a stream URL via an audio provider, cache it in Redis (yt-dlp resolution
is slow), and proxy the upstream stream back to the client with HTTP Range
support. Only provider ids obtained from providers are accepted — the source id
is validated per provider to prevent SSRF.
"""

import json
import re
from collections.abc import AsyncIterator
from http import HTTPStatus

import httpx
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.redis import redis_client
from app.core.security import sha256_hex
from app.providers import base, registry

# Only ids safe to put in a URL path segment are previewable; a provider whose
# source id is a full URL (e.g. SoundCloud) would need a different transport.
_SOURCE_ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "youtube_music": re.compile(r"^[\w-]{11}$"),
}


def _validate(provider: str, source_id: str) -> None:
    pattern = _SOURCE_ID_PATTERNS.get(provider)
    if pattern is None or pattern.match(source_id) is None:
        raise AppError(HTTPStatus.NOT_FOUND, "unknown_provider")


async def resolve_stream(provider: str, source_id: str) -> base.StreamInfo:
    settings = get_settings()
    key = f"providers:stream:{provider}:{sha256_hex(source_id)}"
    cached = await redis_client.get(key)
    if cached is not None:
        try:
            return base.StreamInfo.model_validate(json.loads(cached))
        except ValueError:
            pass

    info = await _resolve_uncached(provider, source_id)
    await redis_client.set(
        key,
        json.dumps(info.model_dump(mode="json")),
        ex=settings.providers_stream_cache_ttl_seconds,
    )
    return info


async def _resolve_uncached(provider: str, source_id: str) -> base.StreamInfo:
    source = base.AudioSource(provider=provider, source_id=source_id)
    for audio in registry.enabled_audio():
        if audio.name == provider:
            try:
                return await audio.resolve_stream(source)
            except Exception as exc:
                raise AppError(HTTPStatus.BAD_GATEWAY, "preview_resolve_failed") from exc
    raise AppError(HTTPStatus.NOT_FOUND, "unknown_provider")


async def build_response(
    provider: str, source_id: str, range_header: str | None
) -> StreamingResponse:
    _validate(provider, source_id)
    info = await resolve_stream(provider, source_id)

    upstream_headers = dict(info.headers)
    if range_header:
        upstream_headers["Range"] = range_header

    client = httpx.AsyncClient(
        timeout=get_settings().providers_timeout_seconds, follow_redirects=True
    )
    req = client.build_request("GET", info.url, headers=upstream_headers)
    upstream = await client.send(req, stream=True)

    if upstream.status_code >= 400:
        await upstream.aclose()
        await client.aclose()
        raise AppError(HTTPStatus.BAD_GATEWAY, "preview_failed")

    response_headers: dict[str, str] = {
        "Content-Type": upstream.headers.get("content-type", "application/octet-stream"),
        "Accept-Ranges": "bytes",
    }
    if upstream.headers.get("content-range"):
        response_headers["Content-Range"] = upstream.headers["content-range"]
    if upstream.headers.get("content-length"):
        response_headers["Content-Length"] = upstream.headers["content-length"]

    async def body() -> AsyncIterator[bytes]:
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(body(), status_code=upstream.status_code, headers=response_headers)
