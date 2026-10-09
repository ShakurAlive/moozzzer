# ADR 0002 — Плагинная система провайдеров и preview-стриминг

Статус: принято (задача 4.1, 4.7). Код: [backend/app/providers](../../backend/app/providers),
[backend/app/services](../../backend/app/services).

## Контекст

Поиск и предпрослушивание работают с внешними площадками (YouTube Music, SoundCloud, позже Deezer/
iTunes/Spotify). Нужен единый способ добавлять площадки и не дать одному сломавшемуся провайдеру
уронить весь поиск.

## Решения

| # | Решение | Почему |
|---|---|---|
| 1 | Два интерфейса в `providers/base.py`: `MetadataProvider.search(query, limit)` и `AudioProvider.find_source/resolve_stream/download`. Модели — `TrackCandidate`, `AudioSource`, `StreamInfo` | единый контракт; Qwen пишет новые провайдеры «по образцу» (`youtube_music.py`) |
| 2 | Включение провайдеров через env `PROVIDERS_METADATA` / `PROVIDERS_AUDIO` (списки ключей) | не трогать код при смене состава площадок |
| 3 | Реестр `registry.py` запускает провайдеры с общим `asyncio.timeout` и изолирует ошибки (`try/except` на провайдер) | падение одного провайдера не ломает поиск |
| 4 | Все блокирующие вызовы (ytmusicapi, yt-dlp) — через `asyncio.to_thread` | библиотеки синхронные |
| 5 | Кэш результатов поиска и разрешённых стрим-URL в Redis с TTL | yt-dlp-резолв медленный; не резолвить повторно |
| 6 | **SSRF-защита:** в yt-dlp/HTTP идут только id, полученные от провайдера; в preview-эндпоинте `source_id` валидируется по паттерну провайдера | не дать пользователю сканировать сеть через прокси |
| 7 | Preview: `GET /preview/{provider}/{source_id}` — резолв → кэш → проксирование через `httpx` с пробросом `Range` (206/`Content-Range`) | `<audio>` просит Range при seek |

## Preview-стриминг и авторизация

`/preview` защищён Bearer-токеном. Web проигрывает превью через `fetch → Blob → object URL` (без
seek), потому что `<audio>` не умеет слать заголовок `Authorization`. Полноценный стриминг с Range
и seek появится на этапе 3.1 через **подписанные короткоживущие URL** (единый механизм для web и mobile).

## Ограничение

Preview по path-параметру работает только для провайдеров с path-safe id (сейчас — YouTube Music,
video-id из 11 символов). У SoundCloud `source_id` — это URL, ему нужен другой транспорт; в демо не используется.

## Как добавить провайдера

Чек-лист — [docs/providers.md](../providers.md).
