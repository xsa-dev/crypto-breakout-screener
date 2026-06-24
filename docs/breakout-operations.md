# Breakout operations, safety, and QA guide

This guide covers the local breakout strategy slices implemented in this repository. It is intentionally local-first: no cloud monitoring, no production alerting stack, and no live broker adapter are enabled by this change.

## Setup and safe local execution

1. Install dependencies:
   ```bash
   uv sync
   ```
2. Keep secrets only in `.env` or another approved local secret store. Do not commit `.env`, API keys, bot tokens, local databases, or logs.
3. Run the app process locally:
   ```bash
   uv run python -m src.app
   ```
4. Run the admin web process when needed:
   ```bash
   uv run uvicorn src.web.__main__:app --host 0.0.0.0 --port 8000
   ```
5. Breakout execution remains fake/local unless a later OpenSpec change explicitly approves a live adapter. Treat current fake fills as deterministic contract tests, not broker evidence.

## Dry-run and current API/web surfaces

- `src.app.breakout` contains the breakout strategy primitives: data normalization, level detection, setup scoring, entry lifecycle, risk checks, fake execution, and local health checks.
- `src.web` remains the existing local FastAPI admin surface for the template. This change does not add a new operator dashboard.
- The safe execution path is dry-run/fake execution only. Live broker credentials and concrete live adapters are out of scope.

## Health and degraded mode

`HealthMonitor` in `src/app/breakout/health.py` evaluates local checks and produces a `HealthReport` with machine-readable reasons.

Checks implemented:

- `market_data`: degraded when the latest market snapshot is missing or older than the configured max age.
- `config`: degraded when config validation errors are supplied by startup/config loading code.
- `fake_broker_state`: degraded when fake adapter reconciliation differs from the expected local snapshot.
- `risk_stop`: degraded when daily loss or max-position limits are already reached.

When a report is degraded, `risk_state_from_report()` merges reasons into `RiskState`. `RiskManager.evaluate()` rejects new entries with explicit reasons such as `feed_degraded`, `config_invalid`, `broker_state_mismatch`, or `health_degraded`.

## Feed-gap runbook

When a feed-gap or stale-market-data degraded reason appears:

1. Stop creating new entry intents; degraded risk state blocks approvals.
2. Inspect the timestamp of the latest normalized snapshot and compare it with local UTC time.
3. Check provider/websocket logs for reconnects, rate limits, and parse errors.
4. Verify the configured symbol/timeframe still matches the data source.
5. Restart only the affected local process after confirming no live broker adapter is enabled.
6. Resume only after a fresh snapshot produces a healthy `market_data` check.

## Restart/reconnect and fake-state reconciliation

For fake execution state mismatches:

1. Compare `FakeExecutionAdapter.reconcile()` with the expected stored snapshot used by the caller.
2. Do not submit new entries while `fake_broker_state_mismatch` is present.
3. Rebuild expected local state from deterministic orders/fills or clear the fake test state only in a local dry-run context.
4. Re-run the health check and relevant tests before continuing.

## Risk-stop and false-breakout handling

- Daily loss and max-position limits are blocking conditions.
- False breakouts are first-class lifecycle transitions in `LifecycleEngine`; after false-breakout detection, close or invalidate the scenario according to the strategy rules before considering a new setup.
- Add-ons must pass the same risk manager and are rejected when they exceed add-on counts, risk budget, or average-price degradation limits.

## Security notes

- `.env`, `.env.*`, local DBs, caches, and logs are ignored by `.gitignore`.
- Use least-privilege exchange keys when future live adapters are approved: no withdrawal permission, testnet/sandbox where possible, narrow IP allowlists if available.
- Rotate any credential that appears in logs, chat, screenshots, or commits. Treat it as compromised.
- Log/error messages should use redaction helpers before including response bodies or exception text that may contain tokens.
- Do not paste authorization headers, private endpoints, or raw API keys into OpenSpec files, docs, tests, or commit messages.
- TLS, backups, production deployment, role separation, and incident response automation require a separate production-hardening change before live operation.

## QA release checklist

Before archiving a breakout implementation slice:

1. Run OpenSpec validation for the change and all specs.
2. Run `uv run ruff check .`.
3. Run `uv run pyright`.
4. Run `uv run pytest`.
5. Review the diff for secret exposure, live-broker side effects, unintended dependency changes, and unrelated files.
6. Confirm live broker execution and production full-auto remain blocked by deferred-scope gates.

## Test methodology and report template

Use deterministic unit tests for strategy contracts. For each run, record:

- Change id and commit hash.
- Commands executed and pass/fail result.
- Any skipped checks and exact reason.
- Risk/security review notes.
- Whether live trading, cloud delivery, push, MR, or merge were performed.

Current local test focus for this change:

- Degraded feed/config state blocks risk approval with explicit reasons.
- Fake adapter mismatch becomes a blocking broker-state degraded reason.
- Daily-loss risk stop produces a degraded health report.
- Secret redaction removes known tokens from log-safe strings.

## Config changelog expectations

When changing risk, entry, health, or data freshness settings, document:

- Setting name and default.
- Operational effect.
- Migration/backward-compatibility impact.
- Verification command or test covering the change.
