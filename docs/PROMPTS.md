# Промпты для ИИ-агентов

## Как работать
1. Берёте задачу из [ROADMAP.md](ROADMAP.md).
2. Копируете **шаблон** ниже, подставляете поля, прикладываете указанные файлы.
3. Агент работает в отдельной ветке → PR → CI → (для критичных задач) ревью Opus → merge → автодеплой.

**Opus** (ограничены токены/права): давать только нужные файлы, просить план до кода в больших задачах, просить сразу писать «образец» для Qwen.
**Qwen (локально)**: одна маленькая задача, всегда давать **файл-образец**, точный список файлов, явный формат ответа. Если отвечает плохо — переведите промпт на английский.

### Какую локальную модель брать (RTX 4070 Super 12 GB + 64 GB RAM)
| Задача | Модель |
|---|---|
| Серия «по образцу» в 2+ файлах (провайдеры, CRUD-эндпоинты + тесты, страницы) | Qwen3-Coder-Next |
| Агентный цикл «написал → запустил тесты → починил» | Qwen3-Coder-Next |
| Первичное ревью PR перед Opus (экономия токенов) | Qwen3-Coder-Next |
| Один компонент / один файл, стили, i18n, конфиги, мелкие фиксы | Qwen2.5-Coder-14B |
| Автодополнение (FIM) в редакторе | Qwen2.5-Coder-14B (или 1.5B/7B для скорости) |
| Архитектура, безопасность, аудио-пайплайн, CI/CD | **только Opus** |

Настройки:
- **Контекст ≥ 32k.** В Ollama по умолчанию он маленький — модель молча обрезает AGENTS.md и образец и начинает «фантазировать». Задайте `num_ctx` / `OLLAMA_CONTEXT_LENGTH`.
- **Qwen2.5-Coder-14B**: Q4_K_M целиком в GPU, контекст ~16–32k (KV-кэш q8_0, чтобы влезло в 12 GB).
- **Qwen3-Coder-Next** (MoE): в llama.cpp держите внимание в GPU, экспертов — в RAM (`--n-cpu-moe N` или `-ot ".ffn_.*_exps.=CPU"`), квант Q4_K_M, контекст 64k. Она медленнее, но заметно лучше держит многофайловые задачи и tool-calling.
- Две модели одновременно в 12 GB не поместятся — работайте с одной за раз.
- Temperature 0.2–0.3 для кода.

---

## Шаблон A — универсальный (для любого агента)
```
Ты — senior-разработчик проекта Moozzzer. Сначала прочитай AGENTS.md — это обязательные правила.

## Задача <номер>: <название>
<1–3 предложения: что и зачем>

## Контекст
- Этап: <N>. Уже готово: <что есть>
- Файлы для изучения: <список путей>
- Образец, которому следовать: <путь или "нет">

## Требования
- <конкретный пункт>
- <конкретный пункт>

## Scope
Можно создавать/менять: <пути>
НЕЛЬЗЯ менять: миграции, providers/base.py, чужие роутеры, <другое>

## Критерии приёмки
- <проверяемый пункт: команда / запрос / поведение>
- Тесты: <какие>

## Формат результата
1. Краткий план (3–7 пунктов)
2. Код (полные файлы или diff)
3. Как проверить вручную
4. Риски / что не сделано / новые зависимости
```

## Шаблон B — для Qwen (короткий, строгий)
```
Read AGENTS.md rules first. Follow the EXAMPLE file exactly in structure and style.

TASK: <одно предложение>
EXAMPLE: <путь к файлу-образцу>
CREATE: <пути>
MODIFY: <пути, и что именно добавить>
DO NOT TOUCH: anything else.
INPUT CONTRACT: <схема/тип/эндпоинт, вставить прямо сюда>
DONE WHEN: <команда тестов> passes.
OUTPUT: full content of each file, nothing else.
```

## Шаблон C — ревью (Opus)
```
Ты — ревьюер проекта Moozzzer. Правила — AGENTS.md. Проверь PR <ссылка/diff>.
Задача PR: <номер и текст из ROADMAP>.
Проверь: соответствие задаче и scope; безопасность (OWASP: инъекции, авторизация на каждом эндпоинте,
утечки путей файлов, SSRF в провайдерах); корректность async/транзакций; тесты; совместимость с arm64.
Ответ: список проблем по приоритету [blocker/major/minor] с файлом и строкой + конкретный фикс.
Не переписывай код целиком.
```

---

## Готовые промпты для ключевых задач

### 0.2 — Скелет монорепо [OPUS]
```
Прочитай AGENTS.md. Репозиторий пустой (есть только AGENTS.md и docs/).

Задача 0.2: создать скелет монорепо Moozzzer, который поднимается одной командой локально
и собирается в arm64-образы для прода.

Требования:
- backend/: FastAPI, pyproject.toml (uv или poetry — выбери и обоснуй), app/main.py с GET /api/health
  (проверяет БД и Redis), app/core/config.py (pydantic-settings), структура папок из AGENTS.md (пустые __init__.py),
  Alembic инициализирован (async), pytest + 1 тест health.
- apps/web/: Vite + React + TS strict + Tailwind + ESLint/Prettier, страница-заглушка, вызывающая /api/health.
- Dockerfiles: multi-stage, непривилегированный пользователь, slim-образы, поддержка linux/arm64.
  Отдельный target "worker" для backend (тот же образ, другая команда; ffmpeg установлен).
- docker-compose.yml (dev): postgres, redis, api (hot reload), worker, web (vite dev). Volumes для данных.
- deploy/docker-compose.prod.yml: те же сервисы из образов ghcr.io/<owner>/moozzzer-*:<tag>, caddy
  (отдаёт web-статику и проксирует /api), healthchecks, restart: unless-stopped, лимиты памяти.
- deploy/Caddyfile: домен из env (DOMAIN=moozzzer.ekroll.app), HTTPS через Let's Encrypt (HTTP-01), security headers, gzip/zstd.
  DNS в Cloudflare в режиме "DNS only" — Caddy сам получает сертификат.
- .env.example, .gitignore, .dockerignore, Makefile (up, down, lint, test, migrate, gen-client).

Критерии: `make up` → http://localhost:5173 показывает "API: ok". `make test` зелёный.
Формат: план → файлы → как проверить → риски.
```

### 0.3 — CI/CD [OPUS]
```
Прочитай AGENTS.md, Makefile, Dockerfiles, deploy/docker-compose.prod.yml.

Задача 0.3: GitHub Actions.
- .github/workflows/ci.yml: на PR и push — backend (ruff, mypy, pytest с сервисами postgres/redis),
  web (eslint, tsc, build). Кэш зависимостей.
- .github/workflows/deploy.yml: на push в main — build & push образов api/worker/web в GHCR
  (linux/arm64; runner ubuntu-24.04-arm, fallback — QEMU), теги sha и latest; затем SSH на сервер
  (secrets: SSH_HOST, SSH_USER, SSH_KEY), docker compose pull, alembic upgrade head, up -d,
  проверка /api/health с ретраями; при провале — откат на предыдущий тег.
- Scheduled workflow раз в неделю: пересборка worker с обновлённым yt-dlp.
- deploy/README.md: какие секреты и какая подготовка сервера нужны (коротко).
Не храни секреты в репо. Используй concurrency, чтобы деплои не пересекались.
```

### 1.1 — Схема БД [OPUS]
```
Прочитай AGENTS.md и раздел "Схема БД" в docs/ROADMAP.md.

Задача 1.1: спроектировать и реализовать модели SQLAlchemy 2 (async, typed Mapped[]) для всего проекта
и одну начальную миграцию Alembic.
- Проверь черновик схемы, исправь слабые места (индексы, каскады, ограничения, enum'ы), обоснуй изменения.
- Сортировка в плейлистах — без пересчёта всех позиций при вставке.
- Триггер-логику orphaned_at реализуй в сервисном слое, а не в БД-триггерах (опиши функции-заглушки).
- Создай docs/adr/0001-db-schema.md (коротко: решения и почему).
Scope: backend/app/db/**, backend/migrations/**, docs/adr/**.
Критерии: alembic upgrade head / downgrade base проходят на чистой БД; тест, создающий по одной записи каждой таблицы.
```

### 4.1 — Интерфейс провайдеров + эталон [OPUS]
```
Прочитай AGENTS.md, docs/ROADMAP.md (раздел "Провайдеры"), backend/app/core/config.py.

Задача 4.1: плагинная система провайдеров.
- backend/app/providers/base.py: Protocol/ABC MetadataProvider (search(query, limit) -> list[TrackCandidate]),
  AudioProvider (find_source(candidate) -> AudioSource | None, resolve_stream(source) -> StreamInfo,
  download(source, dest_dir) -> Path). Pydantic-модели TrackCandidate, AudioSource, StreamInfo.
- registry.py: включение провайдеров через env (PROVIDERS_METADATA=..., PROVIDERS_AUDIO=...),
  общий таймаут, перехват ошибок (падение одного провайдера не ломает поиск), кэш результатов в Redis (TTL).
- providers/youtube_music.py: ЭТАЛОННАЯ реализация обоих интерфейсов (ytmusicapi для поиска, yt-dlp для
  резолва/скачивания; синхронные вызовы — через asyncio.to_thread). Пиши её максимально чисто и
  с комментариями-ориентирами: по ней Qwen будет писать остальные провайдеры.
- Тесты с замоканными ответами (без сети).
- docs/providers.md: чек-лист "как добавить провайдер" (5–10 пунктов) — это инструкция для Qwen.
Безопасность: никаких URL от пользователя в yt-dlp напрямую — только id, полученные от провайдера (защита от SSRF).
```

### 4.3 — Провайдер Deezer [QWEN] (пример шаблона B)
```
Read AGENTS.md rules first. Follow the EXAMPLE file exactly in structure and style.

TASK: Implement Deezer metadata provider (search only, no audio).
EXAMPLE: backend/app/providers/youtube_music.py and docs/providers.md
CREATE: backend/app/providers/deezer.py, backend/tests/providers/test_deezer.py
MODIFY: backend/app/providers/registry.py — register "deezer" exactly like "youtube_music".
DO NOT TOUCH: anything else.
INPUT CONTRACT: Deezer public API GET https://api.deezer.com/search?q=<query>&limit=<n>
  response: data[].{id, title, duration (sec), explicit_lyrics, artist.name, album.title, album.cover_xl, isrc?}
  Map to TrackCandidate from backend/app/providers/base.py. Use httpx.AsyncClient with timeout from settings.
DONE WHEN: `make test` passes; test uses mocked httpx (respx), no real network.
OUTPUT: full content of each file, nothing else.
```

### 2.4 — UI-компонент [QWEN] (пример)
```
Read AGENTS.md rules first. Follow the EXAMPLE file exactly in structure and style.

TASK: Create TrackRow component: cover 40px, title, artist, explicit badge "E", duration, hover shows play button
  over cover, active state when track is playing (animated equalizer icon), "..." menu button on the right.
EXAMPLE: apps/web/src/components/ui/PlaylistCard.tsx (tokens, motion presets, props style)
CREATE: apps/web/src/components/TrackRow.tsx
PROPS: { track: TrackDto (from @moozzzer/api-client); isActive: boolean; isPlaying: boolean;
         onPlay(): void; onMenu(e: React.MouseEvent): void }
RULES: Tailwind classes only, motion presets from apps/web/src/lib/motion.ts, no new dependencies, no `any`.
DONE WHEN: `pnpm -C apps/web lint && pnpm -C apps/web tsc --noEmit` passes.
OUTPUT: full file content only.
```

---

## Порядок запуска (кратко)
```
Этап 0: ВЫ(0.1) → OPUS(0.2) → OPUS(0.3) → ВЫ(0.4) → QWEN(0.5)
Этап 1: OPUS(1.1) → OPUS(1.2) → QWEN(1.3, 1.4, 1.5 параллельно) → [OPUS 1.6 позже]
Этап 2: OPUS(2.1) → QWEN(2.2, 2.4, 2.5) + OPUS(2.3)
Этап 3: OPUS(3.1) → OPUS(3.3) + QWEN(3.2, 3.4, 3.5) → OPUS(3.6)
Этап 4: OPUS(4.1) → OPUS(4.2) + QWEN(4.3–4.6 по образцу) → OPUS(4.7) → QWEN(4.8)
Этап 5: OPUS(5.1, 5.2) → QWEN(5.3–5.5) → ревью OPUS
Этап 6+: см. ROADMAP
```
Правило экономии Opus: каждый раз, когда Opus делает задачу «первой в серии», просите его оставить
**образец + чек-лист** — дальше серию закрывает Qwen, а Opus только ревьюит.
