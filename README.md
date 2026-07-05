# SCNR Pro Boy

Локальный Python-проект для крипто-скринера, торгового робота и исследования breakout-стратегии. Репозиторий уже не является только стартовым шаблоном: в нём есть исходный Bybit pump screener/tradebot, FastAPI-админка, SQLite-журналы, OpenSpec-контракты и отдельный блок deterministic breakout research/backtesting.

Проект рассчитан на локальную разработку и проверку гипотез. Live/full-auto breakout execution не включён: текущие breakout-модули используют локальную/fake execution модель, пока отдельный OpenSpec change явно не разрешит live adapter.

## Быстрый старт

Требования:

- Python `>=3.13`;
- `uv` как менеджер окружения и команд;
- заполненный `.env` только если нужны Bybit-ключи, Telegram-алерты или пароль админки.

Установка зависимостей:

```bash
uv sync
```

Проверки качества:

```bash
uv run ruff check .
uv run pyright
uv run pytest
```

Не устанавливай зависимости через `pip install` и не редактируй dependency list вручную: для этого используется `uv add`, `uv add --dev` и `uv remove`.

## Переменные окружения и секреты

Скопируй пример окружения и заполни только нужные значения:

```bash
cp .env.example .env
```

Основные переменные описаны в `.env.example` и `src/core/env.py`:

- `DB_PATH` — путь к SQLite-файлу, по умолчанию `app.db`;
- `ADMIN_PASSWORD` — пароль входа в web admin;
- `ADMIN_SESSION_SECRET` — секрет подписи cookie-сессии;
- `BYBIT_API_KEY`, `BYBIT_API_SECRET` — ключи Bybit API для credentialed tradebot path;
- `TG_BOT_TOKEN`, `TG_CHAT_ID` — Telegram-алерты.

Не коммить `.env`, API keys, bot tokens, локальные DB-файлы, логи и generated artifacts. В README и OpenSpec-файлах указываются только имена переменных, без реальных значений.

## Runtime: торговый робот и web admin

В репозитории два независимых процесса, которые разделяют SQLite-файл.

Запуск торгового робота:

```bash
uv run python -m src.app
```

`src/app/__main__.py` поднимает producer, consumer и `SignalManager`: данные приходят с Bybit, скринер ищет пампы, решения и попытки входа пишутся в БД. Без Bybit-ключей торговая часть не выставляет реальные ордера; скринер и журналы остаются полезны для наблюдения. Реальная торговля дополнительно управляется настройкой `trading_enabled` в админке.

Запуск FastAPI-админки:

```bash
uv run uvicorn src.web.__main__:app --host 0.0.0.0 --port 8000
```

Админка использует пароль из `ADMIN_PASSWORD` и signed cookie через `ADMIN_SESSION_SECRET`. Основные страницы:

- `/` — runtime settings singleton `settings`;
- `/signals` — последние сигналы скринера;
- `/trades` — последние попытки входа в сделки.

## Breakout research и backtesting

Breakout-блок находится в `src/app/breakout/`. Он покрывает локальную стратегическую основу: нормализацию данных, поиск уровней, scoring, entry lifecycle, risk checks, fake execution, health/degraded-mode проверки и deterministic backtest reports.

Основные experiment entrypoints:

```bash
# Одиночный public-data crypto backtest / downloader
uv run python -m src.app.breakout.experiments.crypto_backtest --help

# Batch research по BTCUSDT public data
uv run python -m src.app.breakout.experiments.crypto_batch --help

# Shared-bankroll portfolio batch по crypto universe
uv run python -m src.app.breakout.experiments.crypto_portfolio_batch --help

# Revalue batch summaries under realistic costs
uv run python -m src.app.breakout.experiments.realistic_cost_profile_search --help
```

Типичные output-директории:

- `artifacts/backtests/` — одиночные backtest reports и CSV/JSON exports;
- `artifacts/batch-backtests/` — batch summaries;
- `artifacts/batch-market-data/` и `artifacts/market-data/` — локальные public market data datasets;
- `artifacts/realistic-cost-profile-search/` — realistic-cost revaluation results.

Generated artifacts нужны для локального research workflow, но не являются секретами и не должны автоматически попадать в коммиты без отдельного решения.

## Где что лежит

- `AGENTS.md` — правила для AI-агентов, архитектурные ограничения и course conventions.
- `CLAUDE.md` — входная инструкция для Claude Code, ссылается на `AGENTS.md`.
- `pyproject.toml` — зависимости, Python `>=3.13`, Ruff и Pyright настройки.
- `.env.example` — список environment variables без секретов.
- `src/core/` — инфраструктура: config, env, logger, enums, schemas, DTOs и общие utils.
- `src/database/` — SQLite/SQLAlchemy async слой: settings, signals, trades, breakout audit/replay tables.
- `src/app/screener/` — producer/consumer Bybit pump screener.
- `src/app/tradebot/` — `SignalManager`, sizing/calculation и Bybit tradebot flow.
- `src/app/breakout/` — breakout strategy foundation, risk/entry/execution/backtesting/research modules.
- `src/app/breakout/experiments/` — CLI entrypoints для public crypto research и batch runs.
- `src/web/` — FastAPI/Jinja web admin.
- `tests/` — pytest coverage для tradebot/breakout contracts, reports, persistence, operations docs.
- `docs/breakout-operations.md` — local operations, degraded mode, security notes, runbook и QA checklist.
- `openspec/` — OpenSpec changes/specs, которые задают scope для нетривиальных изменений.

## OpenSpec и документация

Нетривиальные изменения в проекте идут через OpenSpec: сначала proposal/design/tasks/spec delta, затем review/GO, потом implementation. Активные и архивные контракты лежат в `openspec/changes/` и `openspec/specs/`.

Для breakout-операций смотри:

- `docs/breakout-operations.md` — локальная эксплуатация, degraded-mode checks, dry-run/fake execution, security notes, runbook, QA methodology;
- `openspec/specs/breakout-runtime-and-data/spec.md` — runtime/data contracts;
- `openspec/specs/breakout-backtesting-reporting/spec.md` — backtesting/reporting contracts;
- `openspec/specs/breakout-research-hypothesis-governance/spec.md` — правила evidence tiers и research governance;
- `openspec/specs/breakout-operations-security-docs/spec.md` — operations/security docs contract.

## Safety / limitations

- Credentialed Bybit tradebot path относится к исходному pump screener/tradebot и требует явных API keys плюс включённый `trading_enabled`.
- Breakout execution сейчас local/fake. Не считай fake fills broker evidence.
- Full-auto breakout mode, live broker adapter, production deployment, TLS, backups, role separation и incident automation требуют отдельных OpenSpec changes.
- При feed gap, config error, fake broker mismatch или risk-stop degraded state новые breakout entries должны блокироваться; подробный runbook — в `docs/breakout-operations.md`.
- Любые реальные ключи, authorization headers, private endpoints и tokens нельзя вставлять в README, OpenSpec, logs, tests или commit messages.
