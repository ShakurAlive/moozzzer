# Requires GNU make + POSIX shell (Linux/macOS, WSL or Git Bash on Windows).
COMPOSE      ?= docker compose
RUN_API      := $(COMPOSE) run --rm --no-deps api
RUN_API_DEPS := $(COMPOSE) run --rm api
RUN_WEB      := $(COMPOSE) run --rm --no-deps web
CLIENT_DIR   := packages/api-client

.PHONY: help env up down logs build lint lint-backend lint-web format test migrate revision gen-client

help:
	@echo "up | down | logs | build | lint | format | test | migrate | revision m=msg | gen-client"

env:
	@test -f .env || cp .env.example .env

up: env
	$(COMPOSE) up -d --build
	@echo "web: http://localhost:5173  api: http://localhost:8000/api/docs"

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

build:
	$(COMPOSE) build

lint: lint-backend lint-web

lint-backend: env
	$(RUN_API) sh -c "ruff format --check . && ruff check . && mypy"

lint-web: env
	$(RUN_WEB) sh -c "pnpm lint && pnpm typecheck"

format: env
	$(RUN_API) sh -c "ruff format . && ruff check --fix ."
	$(RUN_WEB) pnpm format

test: env
	$(RUN_API_DEPS) pytest -p no:cacheprovider

migrate: env
	$(RUN_API_DEPS) alembic upgrade head

revision: env
	$(RUN_API_DEPS) alembic revision --autogenerate -m "$(m)"

# Dumps OpenAPI schema and generates TS types (full client package: task 1.4).
gen-client: env
	mkdir -p $(CLIENT_DIR)/src
	$(COMPOSE) run --rm --no-deps -T api python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > $(CLIENT_DIR)/openapi.json
	npx --yes pnpm@10 -C $(CLIENT_DIR) install --frozen-lockfile
	npx --yes pnpm@10 -C $(CLIENT_DIR) run generate
