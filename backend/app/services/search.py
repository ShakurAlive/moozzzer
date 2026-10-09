"""Search aggregation (stage 4.2): run providers in parallel, dedup, rank.

The fan-out + caching lives in ``app.providers.registry``; here we normalize
across providers: drop duplicates (by ISRC, else artist+title+duration±3s) and
rank by a simple relevance score.
"""

from app.providers import base, registry


def _key(candidate: base.TrackCandidate) -> tuple[str, str]:
    return candidate.artist.strip().lower(), candidate.title.strip().lower()


def _is_duplicate(candidate: base.TrackCandidate, seen: list[base.TrackCandidate]) -> bool:
    for existing in seen:
        if candidate.provider == existing.provider and candidate.source_id == existing.source_id:
            return True
        if candidate.isrc and existing.isrc and candidate.isrc == existing.isrc:
            return True
        if (
            _key(candidate) == _key(existing)
            and candidate.duration_ms is not None
            and existing.duration_ms is not None
            and abs(candidate.duration_ms - existing.duration_ms) <= 3000
        ):
            return True
    return False


def _dedup(candidates: list[base.TrackCandidate]) -> list[base.TrackCandidate]:
    result: list[base.TrackCandidate] = []
    for candidate in candidates:
        if not _is_duplicate(candidate, result):
            result.append(candidate)
    return result


def _score(candidate: base.TrackCandidate, query: str) -> float:
    q = query.strip().lower()
    title = candidate.title.strip().lower()
    score = 0.0
    if title == q:
        score += 2.0
    elif q in title or title in q:
        score += 1.0
    if candidate.cover_url:
        score += 0.5
    if candidate.isrc:
        score += 0.5
    if candidate.duration_ms:
        score += 0.25
    return score


async def search_tracks(query: str, limit: int = 20) -> list[base.TrackCandidate]:
    candidates = await registry.search(query, limit=max(limit * 2, 20))
    ranked = sorted(_dedup(candidates), key=lambda c: _score(c, query), reverse=True)
    return ranked[:limit]
