# implement-breakout-deferred-scope-guards

## Why

The approved `breakout-deferred-scope-gates` capability already requires production `full_auto` activation to be blocked until a dedicated full-auto approval change exists. The current foundation DTO exposes `OperationMode.FULL_AUTO`, but there is no local validation guard that rejects production-style configuration attempts with an explicit reason.

## What Changes

- Add a narrow local guard to breakout strategy configuration so `mode=full_auto` is rejected by default with an explicit deferred-scope approval message.
- Keep `full_auto` available as a machine-readable enum/contract for contract-validation tests and future fake-adapter validation, without enabling production behavior.
- Add focused tests proving default `semi_auto` remains valid and unapproved `full_auto` config fails locally before runtime activation.
- Replace the archived placeholder Purpose for the deferred-scope capability with a concrete domain purpose when the change is archived.

## Non-Goals

- No live broker, MT5, Bybit, exchange, terminal, or production adapter implementation.
- No order submission, cancellation, position querying, or credentialed network behavior.
- No production `full_auto` readiness approval, OOS threshold policy, operator controls, or rollout automation.
- No new UI/dashboard, deployment automation, alert integration, or monitoring system.

## Verification

- `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-deferred-scope-guards --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `uv run pytest`
- `uv run ruff check .`
- `uv run pyright`
- `git diff --check`
