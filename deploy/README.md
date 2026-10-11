# Production deploy

CI/CD lives in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | PR, push (not `main`) | ruff, mypy, alembic, pytest (Postgres/Redis services); eslint, prettier, tsc, vite build |
| `deploy.yml` | push to `main`, manual | CI → build `api`/`worker`/`web` for `linux/arm64` → GHCR (`:<sha>`, `:latest`) → deploy |
| `ytdlp-refresh.yml` | Mon 03:17 UTC, manual | rebuild `worker` from `main` with the newest yt-dlp, tag `<sha>-ytYYYYMMDD`, deploy |
| `deploy-server.yml` | reusable | copies `docker-compose.prod.yml`, `Caddyfile`, `deploy.sh`, writes `.env`, runs `deploy.sh <tag>` |

`deploy.sh` on the server: `pull` → start postgres/redis → `alembic upgrade head` → `up -d` →
check `https://$DOMAIN/api/health` (30 × 5 s). On failure it rolls back to the tag stored in
`/opt/moozzzer/.deploy-tag` (last successful deploy) and the workflow fails.
Deploys never overlap (`concurrency: production`).

> Rollback does **not** revert DB migrations — migrations must stay backward compatible with the previous release.

## GitHub settings

Secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `SSH_HOST` | server IP / hostname |
| `SSH_USER` | `deploy` |
| `SSH_KEY` | private key (ed25519) whose public part is in `~deploy/.ssh/authorized_keys` |
| `SSH_KNOWN_HOSTS` | recommended: output of `ssh-keyscan -t ed25519 <host>` (without it the key is trusted on first use) |
| `PROD_ENV` | full content of the prod `.env` (see `.env.example`: `APP_ENV=prod`, strong `POSTGRES_PASSWORD`, `JWT_SECRET` (>= 32 chars, `openssl rand -base64 48`), `GHCR_OWNER=<lowercase owner>`, `DOMAIN=moozzzer.ekroll.app`, `ACME_EMAIL`) |

Variables (optional): `USE_QEMU=true` — build arm64 images on x64 runners via QEMU if `ubuntu-24.04-arm` is unavailable.

GHCR auth on the server uses the short-lived job `GITHUB_TOKEN` (login → pull → logout), no PAT needed.
Images get `org.opencontainers.image.source`, so packages are linked to the repo automatically.

## Server preparation (Ubuntu, ARM64, once)

```bash
# Docker Engine + compose plugin: https://docs.docker.com/engine/install/ubuntu/
sudo apt-get install -y curl

# Keep Docker data (incl. pg_data, media, caddy_data volumes) on the /data disk
sudo mkdir -p /data/docker
echo '{"data-root": "/data/docker", "log-driver": "json-file"}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Deploy user and project directory
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG docker deploy
sudo install -d -o deploy -g deploy -m 750 /opt/moozzzer
sudo -u deploy install -d -m 700 /home/deploy/.ssh
# put the public key into /home/deploy/.ssh/authorized_keys (chmod 600)
```

Firewall: open 22/tcp, 80/tcp, 443/tcp, 443/udp both in the Oracle Cloud Security List and in
iptables on the instance (Oracle Ubuntu images block everything except 22 by default).
DNS: `A moozzzer.ekroll.app → <server IP>` in Cloudflare, **DNS only** (grey cloud).

The first deploy happens on the next push to `main` (or run `Deploy` manually).

## Manual operations (on the server, as `deploy`)

```bash
cd /opt/moozzzer
cat .deploy-tag                                   # currently deployed tag
./deploy.sh <tag>                                 # redeploy / roll back to any tag in GHCR
docker compose -f docker-compose.prod.yml logs -f api worker

# First admin (password is prompted) and registration invites (code is printed once)
docker compose -f docker-compose.prod.yml exec api python -m app.cli create-admin --email <email> --username <name>
docker compose -f docker-compose.prod.yml exec api python -m app.cli create-invite --days 7
```

`docker login ghcr.io` is needed for manual `./deploy.sh` with a tag that is not pulled yet.

## YouTube cookies (для надёжного воспроизведения)

YouTube блокирует запросы с датацентровых IP (Oracle Cloud) бот-проверкой
(«Sign in to confirm you're not a bot»). Без cookies `android_music`-клиент обходит её
только для части треков. Для стабильного воспроизведения нужны cookies:

1. На своей машине, будучи залогиненным в YouTube, экспортируйте cookies в формате Netscape:
   - расширение «Get cookies.txt LOCALLY» (Chrome/Firefox), либо
   - `yt-dlp --cookies-from-browser chrome --cookies cookies.txt` (локальный yt-dlp).
2. Скопируйте на сервер:
   `scp cookies.txt deploy@<server>:/opt/moozzzer/cookies.txt`
3. Пересоздайте контейнеры (файл подключается как `/data/cookies.txt`):
   `cd /opt/moozzzer && docker compose -f docker-compose.prod.yml up -d --force-recreate api worker`

Cookies протухают — периодически обновляйте файл и пересоздавайте контейнеры.

## Yandex Music (поиск по Яндексу, опционально)

Провайдер `yandex_music` ищет треки через неофициальную библиотеку `yandex-music`
(нужен OAuth-токен). Токен получается интерактивно через Device Flow:

1. На сервере: `cd /opt/moozzzer && docker compose -f docker-compose.prod.yml exec api python -m app.cli yandex-auth`
2. Откройте напечатанный `https://ya.ru/device`, введите код, разрешите доступ.
3. Команда напечатает `YANDEX_MUSIC_TOKEN=<токен>`.
4. Добавьте в `.env`: `YANDEX_MUSIC_TOKEN=<токен>` и `PROVIDERS_METADATA=youtube_music,yandex_music`.
5. Передеплой.
