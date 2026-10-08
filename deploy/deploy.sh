#!/usr/bin/env bash
# Server-side deploy with health check and automatic rollback.
# Usage: GHCR_USER=<user> ./deploy.sh <tag>   (GHCR token on stdin; optional if already logged in)
set -Eeuo pipefail

NEW_TAG="${1:?usage: deploy.sh <tag>}"
[[ "$NEW_TAG" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$ ]] || { echo "invalid tag: $NEW_TAG" >&2; exit 2; }

cd "$(dirname "$(readlink -f "$0")")"
[ -f .env ] || { echo ".env not found in $PWD" >&2; exit 1; }

STATE_FILE=.deploy-tag
HEALTH_RETRIES="${HEALTH_RETRIES:-30}"
HEALTH_DELAY="${HEALTH_DELAY:-5}"
DOMAIN="$(grep -E '^DOMAIN=' .env | tail -n1 | cut -d= -f2- | tr -d "\"' ")"
[ -n "$DOMAIN" ] || { echo "DOMAIN is not set in .env" >&2; exit 1; }
PREV_TAG="$(cat "$STATE_FILE" 2>/dev/null || true)"

compose() { docker compose -f docker-compose.prod.yml "$@"; }
log() { printf '[deploy %s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

if [ -n "${GHCR_USER:-}" ] && [ ! -t 0 ]; then
  docker login ghcr.io -u "$GHCR_USER" --password-stdin >/dev/null
  trap 'docker logout ghcr.io >/dev/null 2>&1 || true' EXIT
fi

healthy() {
  local i
  for ((i = 1; i <= HEALTH_RETRIES; i++)); do
    if curl -fsS --max-time 5 --resolve "${DOMAIN}:443:127.0.0.1" "https://${DOMAIN}/api/health"; then
      echo; return 0
    fi
    log "health attempt $i/$HEALTH_RETRIES failed, retrying in ${HEALTH_DELAY}s"
    sleep "$HEALTH_DELAY"
  done
  return 1
}

rollback() {
  if [ -z "$PREV_TAG" ] || [ "$PREV_TAG" = "$NEW_TAG" ]; then
    log "no previous tag to roll back to"
    return 1
  fi
  log "rolling back to $PREV_TAG (DB migrations are NOT reverted)"
  export TAG="$PREV_TAG"
  compose pull --quiet api worker caddy || true
  compose up -d --remove-orphans
  if healthy; then log "rollback to $PREV_TAG is healthy"; else log "rollback is UNHEALTHY, manual action required"; fi
}

log "deploying $NEW_TAG (previous: ${PREV_TAG:-none})"
export TAG="$NEW_TAG"

compose pull --quiet
compose up -d --wait postgres redis

log "applying migrations"
if ! compose run --rm -T api alembic upgrade head; then
  log "migration failed; running containers were not touched"
  exit 1
fi

compose up -d --remove-orphans
# Caddyfile is a bind mount: pick up changes even if the container was not recreated.
compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile \
  || log "WARNING: caddy reload failed, previous Caddy config stays active"

if healthy; then
  echo "$NEW_TAG" > "$STATE_FILE"
  log "deployed $NEW_TAG"
  docker image prune -af --filter "until=336h" >/dev/null || true
  exit 0
fi

log "health check failed for $NEW_TAG"
compose ps
compose logs --tail=50 api caddy || true
rollback || true
exit 1
