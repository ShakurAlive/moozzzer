# Как добавить провайдера

Образец — `backend/app/providers/youtube_music.py` (метаданные + аудио) и
`backend/app/providers/soundcloud.py` (только аудио). Чек-лист:

1. Создай `backend/app/providers/<name>.py`.
2. Реализуй нужный интерфейс из `providers/base.py` (`MetadataProvider`, `AudioProvider` или оба).
3. `name` — уникальный ключ провайдера: он фигурирует в `PROVIDERS_METADATA`/`PROVIDERS_AUDIO`
   и в `tracks.source_provider` в БД.
4. Все блокирующие вызовы (HTTP, yt-dlp, ytmusicapi, ...) — через `asyncio.to_thread`.
5. Никаких URL от пользователя в yt-dlp/HTTP напрямую — только id, полученные от провайдера (SSRF).
6. Нормализуй метаданные в `TrackCandidate` (`provider`, `source_id`, `title`, `artist`, `album`,
   `duration_ms`, `cover_url`, `isrc`, `explicit`).
7. Зарегистрируй фабрику в `registry.py` (`_METADATA` и/или `_AUDIO`).
8. Добавь юнит-тест с замоканными ответами (без сети) в `backend/tests/providers/`.
9. Если нужны ключи/опции — добавь поля в `config.py` и строки в `.env.example`.
10. Проверь: `make lint test` зелёные.
