# ADR 0001 — Схема БД

Статус: принято (задача 1.1). Код: [backend/app/db/models](../../backend/app/db/models),
миграция [0001](../../backend/migrations/versions/20261008_0001_initial_schema.py).

## Решения

| # | Решение | Почему |
|---|---|---|
| 1 | Enum'ы — `VARCHAR(16)` + `CHECK`, а не нативный `CREATE TYPE` | Значения добавляются/удаляются обычной миграцией (`DROP/ADD CONSTRAINT`); нативный enum нельзя сократить, а `ADD VALUE` нельзя использовать в той же транзакции |
| 2 | UUID PK (`gen_random_uuid()` в БД + `uuid4` в Python); `listen_events.id` — `BIGINT IDENTITY` | id не угадываются и известны до flush; события — самая объёмная таблица, им хватает компактного bigint |
| 3 | Все времена — `timestamptz`, `created_at/updated_at` с `server_default now()` | однозначность TZ между web/mobile/сервером |
| 4 | `users.email` хранится в lower-case (`CHECK email = lower(email)`) + `UNIQUE`; `username` уникален без учёта регистра (`UNIQUE INDEX lower(username)`) | без расширения `citext`; «Mom» и «mom» не сосуществуют |
| 5 | `CHECK password_hash IS NOT NULL OR google_sub IS NOT NULL`; добавлен `users.is_active` | у пользователя всегда есть способ входа; отключение без удаления (удаление каскадно стирает медиатеку) |
| 6 | `invites`: свой UUID PK, хранится `code_hash` (sha256), а не код; `used_by` UNIQUE, `revoked_at`; FK → `SET NULL` | утечка БД не даёт рабочих инвайтов; код показывается админу один раз |
| 7 | `refresh_tokens`: `token_hash` UNIQUE + `family_id` | ротация с детектом повторного использования: reuse отозванного токена → отзыв всей семьи |
| 8 | `tracks`: `UNIQUE(source_provider, source_id)`; `isrc` — индекс, **не** unique, `CHECK` формата | ISRC у площадок бывает неверным — дедуп по нему в сервисе (5.1), а не жёстким ограничением |
| 9 | `CHECK status <> 'ready' OR (file_path, file_size NOT NULL)`; пути — относительно `MEDIA_ROOT`; `bitrate` → `bitrate_kbps` | «готовый» трек без файла невозможен; абсолютные пути не утекают в API |
| 10 | FK `user_library/playlist_tracks → tracks` = `RESTRICT`; `→ users/playlists` = `CASCADE`; `listen_events.track_id` = `SET NULL` | трек может исчезнуть только через GC, когда ссылок нет (защита от гонки GC и повторного сохранения); история прослушиваний переживает удаление файла |
| 11 | Индексы на всех FK со стороны «многих» (`track_id` в library/playlist_tracks/listen_events) + `(user_id, added_at)`, `(user_id, started_at)`; частичный `ix_tracks_orphaned_at WHERE orphaned_at IS NOT NULL` | быстрые проверки «есть ли ссылки» и `ON DELETE`; GC сканирует только сирот |
| 12 | `playlist_tracks`: PK `(playlist_id, track_id)` — трек в плейлисте один раз | проще DnD и API; дубли в семейных плейлистах не нужны |

## Порядок в плейлистах
`position NUMERIC` (произвольная точность) + `UNIQUE (playlist_id, position) DEFERRABLE INITIALLY IMMEDIATE`.
- В конец: `max(position) + 1` (или `1`, если пусто). В начало: `min - 1`.
- Между `a` и `b`: `(a + b) / 2` — меняется **одна** строка.
- Каждая вставка в одну и ту же щель добавляет ~1 бит точности; если `scale(position)` > 20, сервис
  перенумеровывает плейлист `1..n` одним `UPDATE` после `SET CONSTRAINTS ... DEFERRED` (редко, в той же транзакции).
- Конфликт уникальности при гонке двух вставок → ретрай.

## orphaned_at — в сервисном слое
Без триггеров: логика видна в коде, тестируется и не срабатывает неожиданно в миграциях/бэкфилах.
Заглушки в [backend/app/services/track_lifecycle.py](../../backend/app/services/track_lifecycle.py), реализация — задача 3.6:
- `on_track_referenced(track_id)` — после вставки в library/playlist: `orphaned_at = NULL`.
- `on_references_removed(track_ids)` — после удаления ссылок: `orphaned_at = now()`, если ссылок не осталось.
  При каскадных удалениях (плейлист, пользователь) вызывающий сначала собирает `track_ids`.
- `reconcile_orphans()` — ночная страховка: исправляет `orphaned_at` по фактическим ссылкам (ловит пропущенные вызовы).
- `collect_garbage(older_than)` — удаляет строки `tracks` с `orphaned_at < now() - 7d`, перепроверив ссылки; файлы удаляются после commit.
- Гонка «удалил последнюю ссылку» / «добавил новую» снимается `SELECT ... FOR UPDATE` строки трека в обоих путях; FK `RESTRICT` — последний рубеж.

## Миграции и прод
- `0001` только создаёт таблицы/индексы, транзакционно (PG DDL) — при ошибке БД остаётся нетронутой.
- `downgrade` удаляет всё — только для dev/test, на проде не запускать (deploy.sh миграции не откатывает).
- Будущие миграции: только аддитивные изменения в одном релизе (expand → contract в следующем),
  `CREATE INDEX CONCURRENTLY` для больших таблиц.

## Тесты
Отдельная БД `<DATABASE>_test` (или `TEST_DATABASE_URL`), пересоздаётся фикстурой и мигрируется через Alembic
на каждый прогон; фикстура отказывается работать с БД без суффикса `_test`. Тесты проверяют
`downgrade base → upgrade head` и отсутствие расхождений моделей с миграциями (`compare_metadata`).
