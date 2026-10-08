# AGENTS.md — общие правила для всех ИИ-агентов

> Этот файл читает **каждый** агент перед началом работы. Он короткий намеренно.
> Детальный план — [docs/ROADMAP.md](docs/ROADMAP.md). Шаблоны задач — [docs/PROMPTS.md](docs/PROMPTS.md).

## Что за проект
**Moozzzer** — приватный музыкальный сервис для одной семьи (до ~10 пользователей).
Поиск трека по внешним площадкам → прослушивание прямо из результатов → сохранение в
собственную библиотеку на сервере (файл хранится один раз, пока он есть хотя бы у одного пользователя).
Клиенты: web (сейчас), Android/iOS (позже, через Expo/React Native).

## Стек (не менять без задачи от владельца)
| Слой | Технология |
|---|---|
| Backend API | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async) + Alembic |
| Фоновые задачи | arq (Redis) — загрузка/конвертация треков, очистка |
| Аудио | yt-dlp, ffmpeg, mutagen (теги) |
| БД / кэш | PostgreSQL 16, Redis 7 |
| Web | React 18 + TypeScript (strict), Vite, Tailwind CSS, shadcn/ui, Framer Motion, Zustand, TanStack Query |
| Mobile (позже) | Expo (React Native) + react-native-track-player |
| Общий код клиентов | `packages/api-client` — TS-типы, сгенерированные из OpenAPI |
| Инфраструктура | Docker, Docker Compose, Caddy (HTTPS), GitHub Actions, GHCR |
| Сервер | Oracle Cloud Free, **ARM64 (aarch64)**, 2 vCPU, 12 GB RAM, ~200 GB, Ubuntu |

## Структура репозитория
```
backend/            FastAPI-приложение
  app/
    api/v1/         роутеры (тонкие, без бизнес-логики)
    core/           config, security, deps
    db/             модели, сессия
    services/       бизнес-логика
    providers/      плагины площадок (search / audio)
    workers/        задачи arq
  migrations/       alembic
  tests/
apps/web/           React-клиент
apps/mobile/        Expo-клиент (этап 8)
packages/api-client/ сгенерированные типы и fetch-клиент
deploy/             docker-compose.prod.yml, Caddyfile, скрипты
docs/               план, решения (ADR), промпты
```

## Жёсткие правила
1. **Одна задача = одна ветка = один PR.** Ветка: `feat/<stage>-<short-name>`, `fix/...`.
2. **Трогай только файлы из scope задачи.** Нужно изменить что-то за пределами — остановись и опиши это в отчёте.
3. **Контракты неприкосновенны:** схема БД (миграции), OpenAPI-эндпоинты, интерфейсы `providers/base.py`
   меняются только в задачах, где это явно указано.
4. Схема БД меняется **только** через новую миграцию Alembic. Существующие миграции не редактировать.
5. Никаких секретов в коде. Всё через переменные окружения (`.env.example` обновлять при добавлении).
6. Все образы должны собираться под `linux/arm64` (и `linux/amd64` для локальной разработки).
7. Не обходить DRM и защиту контента. Источники аудио — только через провайдеров в `providers/`.
8. Не добавлять новые зависимости без пометки в отчёте с причиной.
9. Коммиты — Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`).

## Code style
- Python: `ruff` (lint + format), `mypy --strict` для `app/`, `pytest` + `pytest-asyncio`. Роутеры тонкие, логика в `services/`.
- TS: `eslint`, `prettier`, `strict: true`, без `any`. Компоненты — функциональные, стили — Tailwind.
- Имена, код, комментарии — на английском. Тексты UI — через i18n-ключи (ru по умолчанию).

## Definition of Done (для любой задачи)
- [ ] `docker compose up` поднимается без ошибок
- [ ] Линтеры и тесты зелёные локально (`make lint test`)
- [ ] Новые эндпоинты покрыты тестами (минимум happy path + 1 ошибка)
- [ ] Если менялся API — перегенерирован `packages/api-client`
- [ ] В PR-описании: что сделано, как проверить, что осталось / риски
