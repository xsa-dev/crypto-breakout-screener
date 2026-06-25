# Change: implement-breakout-addon-rollback-reset

## Why
The approved `breakout-risk-position-execution` capability requires deterministic handling when price rolls back to an add-on level after an add-on. Current local risk/execution primitives approve add-ons and can handle density invalidation, but they do not expose a machine-readable local decision for add-on rollback/reset behavior.

## What Changes
- Add a broker-neutral local add-on rollback decision model and risk-manager helper.
- Record whether the added portion is reduced or held, the `addon_level_rollback` reason, affected quantity, remaining base quantity, and audit metadata.
- Add focused deterministic tests for rollback reduction and non-rollback hold behavior.

## Non-Goals
- No live broker/exchange adapter, order submission, cancellation, or position mutation.
- No UI, persistence, backtest engine, or dependency changes.
- No new permanent OpenSpec capability name; this is a narrow delta under `breakout-risk-position-execution`.

## Verification
- `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-addon-rollback-reset --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `uv run pytest`
- `uv run ruff check .`
- `uv run pyright`
- `git diff --check`
