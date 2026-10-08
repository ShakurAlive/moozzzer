## What was done

<!-- Describe the changes made in this PR -->

## How to test

<!-- Steps to verify the changes:
- How to start the services?
- Which endpoints to call?
- What inputs to provide?
- Expected outputs?

Example:
1. `docker compose up`
2. Call `GET /api/v1/health`
3. Verify response is `{"status": "ok"}`
-->

## Risks / TODO

<!-- Any known issues, limitations, or future work -->

---

### Definition of Done checklist

- [ ] `docker compose up` поднимается без ошибок
- [ ] Линтеры и тесты зелёные локально (`make lint test`)
- [ ] Новые эндпоинты покрыты тестами (минимум happy path + 1 ошибка)
- [ ] Если менялся API — перегенерирован `packages/api-client`
- [ ] В PR-описании: что сделано, как проверить, что осталось / риски
